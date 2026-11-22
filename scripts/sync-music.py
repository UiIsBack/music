#!/usr/bin/env python3
"""Move root MP3s into static/music and fetch missing synced lyrics.

Usage:
    python3 scripts/sync-music.py
    python3 scripts/sync-music.py --no-lyrics
    python3 scripts/sync-music.py --force-lyrics
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from pathlib import Path

try:
    import syncedlyrics
except ImportError:
    syncedlyrics = None

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "static" / "music"

REMASTER = re.compile(r"\s*-\s*(?:\d{4}\s+)?Remaster(?:ed)?(?:\s+\d{4})?$", re.I)


def digest(path: Path) -> str:
    hasher = hashlib.md5()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def identical(left: Path, right: Path) -> bool:
    return left.stat().st_size == right.stat().st_size and digest(left) == digest(right)


def move_sidecar(source: Path, target: Path) -> None:
    source_lrc = source.with_suffix(".lrc")
    if not source_lrc.exists():
        return

    target_lrc = target.with_suffix(".lrc")
    if target_lrc.exists():
        if identical(source_lrc, target_lrc):
            source_lrc.unlink()
    else:
        source_lrc.rename(target_lrc)


def move_downloads() -> tuple[int, int, list[str]]:
    LIBRARY.mkdir(parents=True, exist_ok=True)

    moved = 0
    removed = 0
    conflicts: list[str] = []

    for source in sorted(ROOT.glob("*.mp3")):
        target = LIBRARY / source.name

        if not target.exists():
            source.rename(target)
            move_sidecar(source, target)
            moved += 1
            print(f"moved   {source.name}")
        elif identical(source, target):
            move_sidecar(source, target)
            source.unlink()
            removed += 1
            print(f"removed {source.name} (identical copy already in library)")
        else:
            conflicts.append(source.name)
            print(f"skipped {source.name} (different file already in library)")

    return moved, removed, conflicts


def lyrics_queries(path: Path) -> list[str]:
    artist, separator, rest = path.stem.partition(" - ")
    artist = artist.strip()
    title = (rest if separator else path.stem).strip()
    title = REMASTER.sub("", title).strip()
    title = title.replace("…", "").replace("...", "").strip()
    short_title = title.split(" - ")[0].strip()

    queries = [
        f"{title} - {artist}",
        f"{artist} {title}",
        title,
        f"{title} - {artist}".replace(" & ", " and "),
        f"{short_title} - {artist}",
        short_title
    ]

    return list(dict.fromkeys(query for query in queries if query))


def fetch_lyrics(path: Path, retries: int, verbose: bool) -> str | None:
    assert syncedlyrics is not None

    for query in lyrics_queries(path):
        for attempt in range(retries):
            try:
                result = syncedlyrics.search(query)
            except Exception as error:
                if verbose:
                    print(f"  error {query!r}: {error}", file=sys.stderr)
                result = None

            if result:
                return result.strip() + "\n"

            if attempt < retries - 1:
                time.sleep(1.5)

    return None


def sync_lyrics(force: bool, retries: int, delay: float, verbose: bool) -> tuple[int, int, list[str]]:
    if syncedlyrics is None:
        print(
            "syncedlyrics is not installed. Run: pip install syncedlyrics",
            file=sys.stderr
        )
        return 0, 0, []

    files = sorted(LIBRARY.glob("*.mp3"))
    pending = [path for path in files if force or not path.with_suffix(".lrc").exists()]

    found = 0
    missing: list[str] = []

    for index, path in enumerate(pending, 1):
        print(f"[{index}/{len(pending)}] {path.name}", end=" ", flush=True)
        data = fetch_lyrics(path, retries, verbose)

        if data:
            path.with_suffix(".lrc").write_text(data, encoding="utf-8")
            found += 1
            print("ok", flush=True)
        else:
            missing.append(path.name)
            print("no lyrics found", flush=True)

        if delay and index < len(pending):
            time.sleep(delay)

    return found, len(pending) - found, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-move", action="store_true", help="skip moving root MP3s")
    parser.add_argument("--no-lyrics", action="store_true", help="skip fetching lyrics")
    parser.add_argument("--force-lyrics", action="store_true", help="overwrite existing .lrc files")
    parser.add_argument("--retries", type=int, default=2, help="attempts per search query (default: 2)")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between tracks (default: 0.5)")
    parser.add_argument("--verbose", action="store_true", help="show search errors")
    args = parser.parse_args()

    if not args.no_move:
        moved, removed, conflicts = move_downloads()
        print(f"\nmoved {moved}, removed {removed} duplicate(s), conflicts {len(conflicts)}")
        for name in conflicts:
            print(f"  conflict: {name}")
        print()

    if not args.no_lyrics:
        found, missing_count, missing = sync_lyrics(
            args.force_lyrics, args.retries, args.delay, args.verbose
        )
        print(f"\nlyrics: {found} found, {missing_count} missing")
        for name in missing:
            print(f"  missing: {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
