export default defineNuxtRouteMiddleware(() => {
    const auth = useAuth();

    if (auth.data.value?.user.role !== "sudo") {
        return navigateTo({
            name: "index",
        });
    }
});
