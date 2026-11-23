# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```sh
# create a new project
npx sv create my-app
```

To recreate this project with the same configuration:

```sh
# recreate this project
npx sv@1.7.0 create --template minimal --types ts --no-install .
```

## Adding features

Add features to your project with `sv add`:

```sh
npx sv add
```

For example, to add Tailwind CSS:

```sh
npx sv add tailwindcss
```

## Music library

Downloaded MP3s belong in `static/music`. To copy new downloads from the project root into the library and fetch any missing synced lyrics:

```sh
npm run music:sync
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```sh
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building & Deployment

The project supports both **Cloudflare (via Wrangler)** and **Vercel**.

### Cloudflare (Wrangler)
- Build for Cloudflare: `npm run build:cf` (or default `npm run build`)
- Preview locally: `npm run preview:wrangler`
- Deploy: `npm run deploy` (or `npm run deploy:cf`)

### Vercel
- Build for Vercel: `npm run build:vercel`
- Preview locally: `npm run preview:vercel`
- Deploy: `npm run deploy:vercel` (or run `vercel deploy` / connect your Git repo to Vercel, which detects Vercel automatically)
