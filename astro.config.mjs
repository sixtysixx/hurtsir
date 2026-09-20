// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
  site: 'https://hurtsir.pages.dev',
  output: 'static',
  devToolbar: { enabled: false },
  integrations: [
    starlight({
      title: ':3',
      description: 'A comprehensive, step-by-step guide for setting up and troubleshooting SirHurt on Roblox.',
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      components: {
        Footer: './src/components/Footer.astro',
      },
      head: [
        // Display face for titles. Matches the RDD page, which already uses Poppins.
        { tag: 'link', attrs: { rel: 'preconnect', href: 'https://fonts.googleapis.com' } },
        {
          tag: 'link',
          attrs: { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'stylesheet',
            href: 'https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&display=swap',
          },
        },
      ],
      social: [{ icon: 'discord', label: 'Discord', href: 'https://discord.gg/sirhurt' }],
      sidebar: [
        { label: 'Quick Start', slug: 'guide/quick-start' },
        {
          label: 'Setup',
          items: [
            { label: 'Preparation & Prerequisites', slug: 'guide/preparation' },
            { label: 'Roblox Settings', slug: 'guide/roblox-settings' },
            { label: 'Execution & Injection', slug: 'guide/injection' },
          ],
        },
        {
          label: 'Fixes',
          items: [
            { label: 'Troubleshooting', slug: 'guide/troubleshooting' },
            { label: 'Downgrade Tutorial', slug: 'guide/downgrade' },
          ],
        },
        { label: 'Downgrade Thingamabob 6000', link: '/rdd/' },
      ],
    }),
  ],
});
