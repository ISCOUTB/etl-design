import type { UseFetchOptions } from "#app";

export function useApi() {
    const runtimeConfig = useRuntimeConfig();
    const auth = useAuth();

    return $fetch.create({
        baseURL: runtimeConfig.public.apiBase,
        onRequest({ options }) {
            const accessToken = auth.data.value?.accessToken;
            if (accessToken) {
                const headers = new Headers(options.headers);
                headers.set("Authorization", `Bearer ${accessToken}`);
                options.headers = headers;
            }
        },
    });
}

export function useApiFetch<T>(url: string | (() => string), options: UseFetchOptions<T> = {}) {
    return useFetch(url, {
        ...options,
        $fetch: useApi(),
    });
}
