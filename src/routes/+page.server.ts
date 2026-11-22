import { readdirSync } from 'node:fs';
import { join } from 'node:path';
import type { PageServerLoad } from './$types';

const REMASTER = /\s*-\s*(?:\d{4}\s+)?Remaster(?:ed)?(?:\s+\d{4})?$/i;

export const load: PageServerLoad = () => {
	const dir = join(process.cwd(), 'static', 'music');

	const tracks = readdirSync(dir)
		.filter((file) => file.toLowerCase().endsWith('.mp3'))
		.map((file) => {
			const name = file.replace(/\.mp3$/i, '');
			const [artist, ...rest] = name.split(' - ');
			const title = (rest.join(' - ') || name).replace(REMASTER, '').trim();

			return {
				artist: artist.trim(),
				title,
				src: `/music/${encodeURIComponent(file)}`
			};
		})
		.sort((a, b) => a.artist.localeCompare(b.artist) || a.title.localeCompare(b.title));

	return { tracks };
};
