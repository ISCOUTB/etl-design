export default defineNuxtRouteMiddleware(() => {
    const { $localeRoute } = useNuxtApp();
    if (!import.meta.dev) {
        return navigateTo($localeRoute({ name: "index" }));
    }
});
