import adapterCloudflare from '@sveltejs/adapter-cloudflare';
import adapterVercel from '@sveltejs/adapter-vercel';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const isVercel = !!process.env.VERCEL || process.env.DEPLOY_TARGET === 'vercel';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			alias: { $lib: 'src/lib' },
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			adapter: isVercel ? adapterVercel() : adapterCloudflare()
		})
	]
});
