export class ApiClient {
    @Singleton()
    static getInstance() {
        const config = useRuntimeConfig();
        return $fetch.create({
            baseURL: config.public.API_BASE,
        });
    }
}
