export default defineNuxtRouteMiddleware((to) => {
    const { callbackUrl } = to.query;

    if (!callbackUrl) {
        return;
    }

    const rawPath = String(callbackUrl);
    const decodedPath = decodeURIComponent(rawPath);

    const isSafe = validateCallbackUrl(decodedPath);

    if (!isSafe) {
        const query = new Map(Object.entries(to.query));
        query.delete("callbackUrl");

        return navigateTo({
            path: to.path,
            query: Object.fromEntries(query),
            replace: true,
        });
    }
});

function parseUrl(path: string) {
    try {
        return new URL(path, "https://internal");
    } catch {
        return null;
    }
}

function validateCallbackUrl(path: string): boolean {
    const { $router } = useNuxtApp();

    const parsed = parseUrl(path);
    if (!parsed) {
        return false;
    }

    if (parsed.origin !== "https://internal") {
        return false;
    }

    const match = $router.resolve(parsed.pathname);
    if (match.matched.length === 0 || match.name === undefined) {
        return false;
    }

    if (parsed.search) {
        return false;
    }

    return true;
}
