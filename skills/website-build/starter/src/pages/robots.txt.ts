import type { APIRoute } from 'astro';
import { site as config } from '../site.config.mjs';

// Before launch the whole site is closed to crawlers (see site.launched).
export const GET: APIRoute = ({ site }) => {
  const sitemap = new URL('sitemap-index.xml', site).href;
  const body = config.launched
    ? `User-agent: *\nAllow: /\n\nSitemap: ${sitemap}\n`
    : `# Pre-launch: not open to search engines yet.\nUser-agent: *\nDisallow: /\n`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
