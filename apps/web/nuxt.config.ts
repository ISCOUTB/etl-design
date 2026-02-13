import process from "node:process";
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
    compatibilityDate: "2025-07-15",
    devtools: { enabled: true },

    ///////////////////////////////////////////////////////
    // CORE CONFIG
    ///////////////////////////////////////////////////////
    css: ["~/assets/css/tailwind.css"],
    vite: {
        plugins: [
            // @ts-expect-error "https://github.com/nuxt/nuxt/issues/34306"
            tailwindcss(),
        ],
    },
    modules: [
        "@nuxt/eslint",
        "shadcn-nuxt",
        "@vueuse/nuxt",
        "@nuxtjs/color-mode",
        "@vite-pwa/nuxt",
        "@nuxtjs/i18n",
    ],
    imports: {
        dirs: [
            "~/composables/**/!(*test|*.spec).{ts,js,mjs,mts}",
            "~/utils/**/!(*test|*.spec).{ts,js,mjs,mts}",
            "~~/shared/utils/**/!(*test|*.spec).{ts,js,mjs,mts}",
        ],
    },
    ignore: ["**/*.test.ts", "**/*.spec.ts"],

    ///////////////////////////////////////////////////////
    // MODULES CONFIG
    ///////////////////////////////////////////////////////
    eslint: { config: { standalone: false } },
    shadcn: {
        prefix: "",
        componentDir: "@/components/ui",
    },
    colorMode: {
        classSuffix: "",
    },
    i18n: {
        baseUrl: process.env.BASE_URL,
        skipSettingLocaleOnNavigate: false,
        detectBrowserLanguage: {
            useCookie: true,
            redirectOn: "no prefix",
            fallbackLocale: "en-US",
        },
        defaultLocale: "en-US",
        strategy: "prefix",
        locales: [
            {
                code: "en-US",
                language: "English",
                file: "en-US.json",
            },
        ],
    },
    pwa: {
        registerType: "autoUpdate",
        manifest: {
            name: "S.L.O.T.H",
            short_name: "S.L.O.T.H",
            description: "Graphical Interface for S.L.O.T.H Framework",
            theme_color: "#000",
            background_color: "#000",
            display: "standalone",
            display_override: ["window-controls-overlay"],
            start_url: "/",
            scope: "/",
            icons: [],
            screenshots: [],
        },
        workbox: {
            cleanupOutdatedCaches: true,
            clientsClaim: true,
            maximumFileSizeToCacheInBytes: 10 * 1024 * 1024,
            globPatterns: [],
            globIgnores: ["**/_payload.json", "_nuxt/builds/**/*.json", "sw.js", "workbox-*.js"],
            runtimeCaching: [
                {
                    urlPattern: ({ sameOrigin, request }) =>
                        sameOrigin && request.mode === "navigate",
                    handler: "NetworkFirst",
                    options: {
                        cacheName: "pages-cache",
                        networkTimeoutSeconds: 3,
                        cacheableResponse: { statuses: [0, 200] },
                    },
                },
                {
                    urlPattern:
                        /\.(?:js|mjs|cjs|mp4|png|webp|svg|ico|css|glb|ttf|webmanifest|txt)$/,
                    handler: "CacheFirst",
                    options: {
                        cacheName: "js-cache",
                        expiration: { maxEntries: 20, maxAgeSeconds: 7 * 24 * 60 * 60 },
                        cacheableResponse: { statuses: [0, 200] },
                    },
                },
            ],
        },
    },

    ///////////////////////////////////////////////////////
    // FLAGS
    ///////////////////////////////////////////////////////
    experimental: {
        payloadExtraction: false,
        appManifest: false,
    },
    nitro: {
        experimental: {
            websocket: true,
        },
    },
});
