export default defineNuxtRouteMiddleware((to, from) => {
    const config = useAppConfig();
    const callbackUrl = from.query[config.constants.CALLBACK_KEY];
    if (callbackUrl && !to.query[config.constants.CALLBACK_KEY]) {
        return navigateTo({
            path: to.path,
            query: {
                ...to.query,
                [config.constants.CALLBACK_KEY]: callbackUrl,
            },
        });
    }
});
