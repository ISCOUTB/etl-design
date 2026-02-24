import type { UseFetchOptions } from "#app";

export function useApi() {
    const runtimeConfig = useRuntimeConfig();
    const auth = useAuth();

    return $fetch.create({
        baseURL: runtimeConfig.public.apiBase,
        onRequest({ options }) {
            const accessToken = auth.data.value?.accessToken;
            if (accessToken) {
                const headers: HeadersInit = {};

                if (options.headers instanceof Headers) {
                    options.headers.forEach((value, key) => (headers[key] = value));
                }

                if (typeof options.headers === "object") {
                    Object.entries(options.headers).forEach(
                        ([key, value]) => (headers[key] = value),
                    );
                }

                headers.Authorization = `Bearer ${accessToken}`;

                options.headers = new Headers(headers);
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
