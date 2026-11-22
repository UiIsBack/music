<script lang="ts">
	import { AudioLines, Pause, Play, SkipBack, SkipForward, Volume2 } from '@lucide/svelte';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const tracks = $derived(data.tracks);

	let audio = $state<HTMLAudioElement | null>(null);

	let current = $state(0);
	let playing = $state(false);
	let time = $state(0);
	let duration = $state(0);
	let volume = $state(80);
	let scrubbing = $state(false);
	let scrubTime = $state(0);

	const track = $derived(tracks[current]);

	type LyricLine = { time: number | null; text: string };

	let lyrics = $state<LyricLine[] | null>(null);
	let lyricsBox = $state<HTMLDivElement | null>(null);
	let lastActiveLyric = -1;

	$effect(() => {
		if (audio) {
		audio.addEventListener("timeupdate", () => {
		  time = audio?.currentTime ?? 0
		})
		audio.volume = volume / 100;}
	});



	$effect(() => {
		const src = track.lrc;
		lyrics = null;
		lastActiveLyric = -1;
		if (!src) return;

		let cancelled = false;
		fetch(src)
			.then((res) => (res.ok ? res.text() : null))
			.then((text) => {
				if (!cancelled && text) lyrics = parseLrc(text);
			})
			.catch(() => {});

		return () => {
			cancelled = true;
		};
	});

	const activeLyric = $derived.by(() => {
		if (!lyrics) return -1;
		let active = -1;
		for (let i = 0; i < lyrics.length; i++) {
			const at = lyrics[i].time;
			if (at === null) return -1;
			if (at <= time) active = i;
			else break;
		}
		return active;
	});

	$effect(() => {
		if (!lyricsBox || activeLyric < 0 || activeLyric === lastActiveLyric) return;
		lastActiveLyric = activeLyric;

		const line = lyricsBox.querySelector<HTMLElement>('[data-active="true"]');
		if (!line) return;

		const box = lyricsBox.getBoundingClientRect();
		const rect = line.getBoundingClientRect();
		lyricsBox.scrollBy({
			top: rect.top - box.top - lyricsBox.clientHeight / 2 + rect.height / 2,
			behavior: 'smooth'
		});
	});

	function parseLrc(text: string): LyricLine[] {
		const timed: LyricLine[] = [];
		const plain: LyricLine[] = [];

		for (const raw of text.split('\n')) {
			const content = raw.replace(/\[[^\]]*\]/g, '').trim();
			if (!content) continue;

			const stamps = [...raw.matchAll(/\[(\d{1,2}):(\d{2}(?:\.\d+)?)\]/g)];
			if (stamps.length === 0) {
				plain.push({ time: null, text: content });
				continue;
			}

			for (const stamp of stamps) {
				timed.push({ time: Number(stamp[1]) * 60 + Number(stamp[2]), text: content });
			}
		}

		return timed.length > 0 ? timed.sort((a, b) => (a.time ?? 0) - (b.time ?? 0)) : plain;
	}

	function formatTime(seconds: number) {
		if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
		const minutes = Math.floor(seconds / 60);
		const rest = Math.floor(seconds % 60);
		return `${minutes}:${rest.toString().padStart(2, '0')}`;
	}

	function start(index: number) {
		if (!audio) return;
		current = index;
		time = 0;
		duration = 0;
		audio.src = tracks[index].src;
		audio.load();
		void audio.play();

	}

	function toggle() {
		if (!audio) return;
		if (!audio.src) {
			audio.src = track.src;
			audio.load();
		}
		if (audio.paused) void audio.play();
		else audio.pause();
	}

	function select(index: number) {
		if (index === current) toggle();
		else start(index);
	}

	function next() {
		start((current + 1) % tracks.length);
	}

	function previous() {
		start((current - 1 + tracks.length) % tracks.length);
	}

	function updateSeek(value: number) {
		scrubbing = true;
		scrubTime = value;
		if (audio) audio.currentTime = value;
	}

	function commitSeek(value: number) {
		if (audio) audio.currentTime = value;
		time = value;
		scrubTime = value;
		scrubbing = false;
	}
</script>

<svelte:head>
	<title> local music</title>
</svelte:head>

<div class="min-h-svh">
	<header class="sticky top-0 z-10 border-b border-border/60 bg-background/80 backdrop-blur-xl">
		<div class="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
			<div class="flex items-center gap-3">
				<div
					class="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"
				>
					<AudioLines class="size-4" />
				</div>
				<div class="leading-tight">
					<h1 class="text-sm font-semibold tracking-tight">Evan {audio}</h1>
					<p class="text-xs text-muted-foreground">Local library</p>
				</div>
			</div>
			<Badge variant="secondary">{tracks.length} tracks</Badge>
		</div>
	</header>

	<main class="mx-auto max-w-5xl px-4 pt-10 pb-40 sm:px-6">
		<div class="mb-6 px-2">
			<h2 class="text-2xl font-semibold tracking-tight">Your music</h2>
			<p class="mt-1 text-sm text-muted-foreground">Pick a track to start listening.</p>
		</div>

		{#if lyrics && lyrics.length > 0}
			<section class="mb-6 overflow-hidden rounded-xl border border-border/60 bg-muted/20">
				<div class="flex items-center justify-between gap-3 border-b border-border/60 px-4 py-3">
					<div class="min-w-0">
						<p class="truncate text-sm font-medium">{track.title}</p>
						<p class="truncate text-xs text-muted-foreground">{track.artist}</p>
					</div>
					<Badge variant="secondary">Lyrics</Badge>
				</div>
				<div bind:this={lyricsBox} class="max-h-72 overflow-y-auto px-4 py-4">
					<div class="space-y-2">
						{#each lyrics as line, i}
							<p
								data-active={i === activeLyric}
								class="text-sm leading-relaxed transition-colors {i === activeLyric
									? 'font-medium text-foreground'
									: 'text-muted-foreground'}"
							>
								{line.text}
							</p>
						{/each}
					</div>
				</div>
			</section>
		{/if}

		<div class="space-y-0.5">
			{#each tracks as t, i (t.src)}
				<button
					type="button"
					onclick={() => select(i)}
					aria-label={`${playing && i === current ? 'Pause' : 'Play'} ${t.title} by ${t.artist}`}
					class="group grid w-full grid-cols-[2rem_minmax(0,1fr)_auto] items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:outline-none {i ===
					current
						? 'bg-muted/40'
						: ''}"
				>
					<span
						class="flex size-7 items-center justify-center text-xs tabular-nums text-muted-foreground"
					>
						{#if i === current && playing}
							<AudioLines class="size-3.5 text-primary" />
						{:else}
							<Play class="hidden size-3.5 group-hover:block" />
							<span class="group-hover:hidden">{i + 1}</span>
						{/if}
					</span>
					<span class="min-w-0">
						<span
							class="block truncate text-sm font-medium {i === current ? 'text-primary' : ''}"
						>
							{t.title}
						</span>
						<span class="block truncate text-xs text-muted-foreground">{t.artist}</span>
					</span>
					<span
						class="text-[11px] text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
					>
						{i === current && playing ? 'Playing' : 'Play'}
					</span>
				</button>
			{/each}
		</div>
	</main>
</div>

<footer
	class="fixed inset-x-0 bottom-0 z-20 border-t border-border/60 bg-background/80 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl"
>
	<div class="absolute inset-x-0 top-0 h-0.5 bg-border md:hidden">
		<div
			class="h-full bg-primary"
			style="width: {duration ? (time / duration) * 100 : 0}%"
		></div>
	</div>

	<div
		class="mx-auto grid max-w-5xl grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-4 py-3 sm:px-6 md:grid-cols-3"
	>
		<div class="flex min-w-0 items-center gap-3">
			<div
				class="flex size-10 shrink-0 items-center justify-center rounded-md border border-border/60 bg-muted text-xs font-semibold text-muted-foreground uppercase"
			>
				{track.artist.charAt(0)}
			</div>
			<div class="min-w-0">
				<p class="truncate text-sm font-medium">{track.title}</p>
				<p class="truncate text-xs text-muted-foreground">{track.artist}</p>
			</div>
		</div>

		<div class="flex items-center justify-end gap-1 md:flex-col md:justify-center md:gap-1.5">
			<div class="flex items-center gap-1">
				<Button
					variant="ghost"
					size="icon-sm"
					onclick={previous}
					aria-label="Previous track"
					class="hidden sm:inline-flex"
				>
					<SkipBack />
				</Button>
				<Button size="icon" class="rounded-full" onclick={toggle} aria-label={playing ? 'Pause' : 'Play'}>
					{#if playing}
						<Pause />
					{:else}
						<Play class="translate-x-px" />
					{/if}
				</Button>
				<Button
					variant="ghost"
					size="icon-sm"
					onclick={next}
					aria-label="Next track"
					class="hidden sm:inline-flex"
				>
					<SkipForward />
				</Button>
			</div>

			<div class="hidden w-full items-center gap-2 md:flex">
				<span class="w-8 text-right text-[11px] tabular-nums text-muted-foreground">
					{formatTime(time)}
				</span>
				<Slider
					type="single"
					min={0}
					max={Math.max(duration, 1)}
					step={0.1}
					value={scrubbing ? scrubTime : time}
					onValueChange={updateSeek}
					onValueCommit={commitSeek}
					disabled={duration === 0}
					aria-label="Seek"
				/>
				<span class="w-8 text-[11px] tabular-nums text-muted-foreground">
					{formatTime(duration)}
				</span>
			</div>
		</div>

		<div class="hidden items-center justify-end gap-2 md:flex">
			<Volume2 class="size-4 text-muted-foreground" />
			<Slider
				type="single"
				min={0}
				max={100}
				step={1}
				bind:value={volume}
				class="w-24"
				aria-label="Volume"
			/>
		</div>
	</div>
</footer>

<audio
	bind:this={audio}
	onplay={() => (playing = true)}
	onpause={() => (playing = false)}
	ontimeupdate={() => {
		if (!scrubbing) time = audio?.currentTime ?? 0;
	}}
	ondurationchange={() => (duration = audio?.duration ?? 0)}
	onended={next}
></audio>
