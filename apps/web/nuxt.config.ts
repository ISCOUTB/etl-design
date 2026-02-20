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
        "@sidebase/nuxt-auth",
        "@vee-validate/nuxt",
    ],
    imports: {
        dirs: [
            "~/composables/**/!(*test|*.spec).{ts,js,mjs,mts}",
            "~/utils/**/!(*test|*.spec).{ts,js,mjs,mts}",
            "~~/shared/utils/**/!(*test|*.spec).{ts,js,mjs,mts}",
        ],
    },
    components: [
        { path: "~/components/", extensions: [".vue"] },
        { path: "~/components/common", pathPrefix: false, extensions: [".vue"] },
    ],
    ignore: ["**/*.test.ts", "**/*.spec.ts"],
    runtimeConfig: {
        auth: {
            secret: process.env.AUTH_SECRET,
            sign: process.env.AUTH_SIGN,
            maxAge: 30 * 24 * 60 * 60,
        },
    },

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
        baseUrl: process.env.HOMEPAGE_URL,
        skipSettingLocaleOnNavigate: false,
        detectBrowserLanguage: {
            useCookie: true,
            redirectOn: "root",
            fallbackLocale: "en",
            alwaysRedirect: true,
        },
        customRoutes: "meta",
        defaultLocale: "en",
        strategy: "prefix",
        locales: [
            {
                code: "en",
                language: "en-US",
                file: "en.json",
                name: "English",
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
    auth: {
        baseURL: process.env.AUTH_ORIGIN,
        provider: {
            type: "authjs",
        },
        sessionRefresh: {
            enablePeriodically: 5 * 60 * 1000,
            enableOnWindowFocus: true,
        },
        globalAppMiddleware: true,
    },
    veeValidate: {
        autoImports: true,
        componentNames: {
            Field: "VeeField",
            FieldArray: "VeeFieldArray",
            Form: "VeeForm",
            ErrorMessage: "VeeErrorMessage",
        },
    },

    ///////////////////////////////////////////////////////
    // FLAGS
    ///////////////////////////////////////////////////////
    experimental: {
        payloadExtraction: false,
        appManifest: false,
        scanPageMeta: true,
    },
    nitro: {
        experimental: {
            websocket: true,
        },
        devProxy: {
            "/sw.js": { target: "/sw.js" },
        },
    },
});
