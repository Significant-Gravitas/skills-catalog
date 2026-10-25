// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import { site } from './src/site.config.mjs';

// `site` must be the live address: it drives canonical links, the sitemap and
// social previews. Update site.url in src/site.config.mjs when the domain changes.
export default defineConfig({
  site: site.url,
  trailingSlash: 'ignore',
  build: { format: 'directory' },
  integrations: [sitemap({ filter: (page) => !/\/(404|thanks)\/?$/.test(page) })],
  vite: { plugins: [tailwindcss()] },
});
