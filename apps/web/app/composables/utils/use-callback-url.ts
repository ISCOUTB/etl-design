import type { RouteLocationRaw } from "vue-router";

export default function (fallback: RouteLocationRaw = "/") {
    const config = useAppConfig();

    const { $localePath } = useNuxtApp();

    const callbackUrl = useRouteQuery(config.constants.CALLBACK_KEY, undefined, {
        transform(value: string) {
            if (!value) {
                return $localePath(fallback);
            }

            try {
                const url = new URL(value.toString(), "https://internal");
                return url.pathname + url.search + url.hash;
            } catch {
                if (value.startsWith("/")) {
                    return value;
                }

                return $localePath(fallback);
            }
        },
    });

    return { callbackUrl, navigate: () => navigateTo(callbackUrl.value) };
}
