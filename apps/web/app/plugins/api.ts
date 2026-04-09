export default defineNuxtPlugin({
    name: "api",
    parallel: true,
    setup() {
        const runtimeConfig = useRuntimeConfig();
        const auth = useAuth();

        return {
            provide: {
                api: $fetch.create({
                    baseURL: runtimeConfig.public.apiBase,
                    onRequest({ options }) {
                        const accessToken = auth.data.value?.accessToken;
                        if (accessToken) {
                            options.headers.set("Authorization", `Bearer ${accessToken}`);
                        }
                    },
                }),
            },
        };
    },
});
