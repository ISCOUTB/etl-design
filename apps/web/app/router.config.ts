import type { RouterOptions } from "nuxt/schema";

export default <RouterOptions>{
    async scrollBehavior(to, from, savedPosition) {
        const nuxtApp = useNuxtApp();

        if (nuxtApp.$i18n && to.name !== from.name) {
            await nuxtApp.$i18n.waitForPendingLocaleChange();
        }

        return savedPosition || { top: 0 };
    },
};
