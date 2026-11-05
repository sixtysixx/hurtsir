// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
  site: "https://sirhurt.pages.dev",
  output: "static",
  devToolbar: { enabled: false },
  // Sidebar/wiki links are the main navigation path: warm the HTML on hover so
  // the next page is already in the browser cache when it is clicked.
  prefetch: { prefetchAll: true, defaultStrategy: "hover" },
  integrations: [
    starlight({
      title: ":3",
      description:
        "A comprehensive, step-by-step guide for setting up and troubleshooting SirHurt on Roblox.",
      favicon: "/favicon.svg",
      customCss: ["./src/styles/custom.css"],
      components: {
        Footer: "./src/components/Footer.astro",
      },
      head: [
        // Display face for titles (Poppins) is self-hosted - see custom.css.
        // Kept in /public/fonts so there is no cross-origin stylesheet or font
        // request blocking first paint. Preload the weight used by headings.
        {
          tag: "link",
          attrs: {
            rel: "preload",
            href: "/fonts/poppins-600.woff2",
            as: "font",
            type: "font/woff2",
            crossorigin: "",
          },
        },
      ],
      social: [
        {
          icon: "discord",
          label: "Discord",
          href: "https://discord.gg/sirhurt",
        },
      ],
      sidebar: [
        { label: "Start Here", slug: "guide/quick-start" },
        {
          label: "Setup",
          items: [
            { label: "1. Prepare Windows", slug: "guide/preparation" },
            { label: "2. Configure Roblox", slug: "guide/roblox-settings" },
            { label: "3. Install SirHurt", slug: "guide/install" },
            { label: "4. Inject", slug: "guide/injection" },
          ],
        },
        {
          label: "If something goes wrong",
          items: [
            { label: "Troubleshooting", slug: "guide/troubleshooting" },
            { label: "Version Mismatch & Downgrade", slug: "guide/downgrade" },
          ],
        },
        { label: "Downgrade Thingamabob 6000", link: "/rdd/" },
        { label: "gifs", link: "/gifz/" },
      ],
    }),
    sitemap({
      filter: (url) => !url.includes('/secretgifs'),
    }),
  ],
});