import type { UseFetchOptions } from "#app";

export function useApi() {
    const runtimeConfig = useRuntimeConfig();
    const auth = useAuth();

    return $fetch.create({
        baseURL: runtimeConfig.public.apiBase,
        onRequest({ options }) {
            const accessToken = auth.data.value?.accessToken;
            if (accessToken) {
                options.headers.set("Authorization", `Bearer ${accessToken}`);
            }
        },
    });
}

export function useApiFetch<T>(url: MaybeRefOrGetter<string>, options: UseFetchOptions<T> = {}) {
    return useFetch(url, { ...options, $fetch: useApi() });
}
