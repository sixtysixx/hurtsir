// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

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
        { label: "Quick Start", slug: "guide/quick-start" },
        {
          label: "Setup",
          items: [
            { label: "Preparation & Prerequisites", slug: "guide/preparation" },
            { label: "Roblox Settings", slug: "guide/roblox-settings" },
            { label: "Execution & Injection", slug: "guide/injection" },
          ],
        },
        {
          label: "Fixes",
          items: [
            { label: "Troubleshooting", slug: "guide/troubleshooting" },
            { label: "Downgrade Tutorial", slug: "guide/downgrade" },
          ],
        },
        { label: "Downgrade Thingamabob 6000", link: "/rdd/" },
        { label: "gifs", link: "/gifz/" },
      ],
    }),
  ],
});
