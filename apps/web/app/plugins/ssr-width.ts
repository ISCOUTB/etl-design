import { provideSSRWidth } from "@vueuse/core";

export default defineNuxtPlugin({
    name: "ssr-width",
    parallel: true,
    setup(nuxtApp) {
        provideSSRWidth(1024, nuxtApp.vueApp);
    },
});
