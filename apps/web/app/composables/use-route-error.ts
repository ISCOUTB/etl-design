import type { WatchStopHandle } from "vue";

interface Args {
    title: string;
    description: string;
}

type RouteErrorArgs = Partial<Args>;
type RouteErrorHandler = (args: RouteErrorArgs) => unknown;
type RouteErrorMap = Partial<Record<ResponseCodes.Code, RouteErrorHandler>>;

function toText<T extends string>(value: unknown): T | undefined {
    if (Array.isArray(value)) {
        return value[0]?.toString();
    }

    if (value == null) {
        return undefined;
    }

    return String(value) as T;
}

export default function () {
    const watchers = useState<Set<WatchStopHandle>>(
        "use-route-error:watchers",
        () => new Set<WatchStopHandle>(),
    );

    const route = useRoute();
    const errorToast = useErrorToast();

    function createQuery() {
        const query = new Map(Object.entries(route.query));

        query.delete("error");
        query.delete("title");
        query.delete("description");

        return query;
    }

    function clearQuery(targetPath?: string) {
        navigateTo({
            path: targetPath ?? route.path,
            query: Object.fromEntries(createQuery()),
        });
    }

    function onMap(map: RouteErrorMap, path?: string) {
        const stopWatcher = watch(
            () => route.query.error,
            (error) => {
                const errorCode = toText<ResponseCodes.Code>(error);
                if (!errorCode) {
                    return;
                }

                const handler = map[errorCode];
                if (!handler) {
                    return;
                }

                handler({
                    title: toText(route.query.title),
                    description: toText(route.query.description),
                });

                clearQuery(path);
            },
            { immediate: true },
        );

        watchers.value.add(stopWatcher);
    }

    function onToast(path?: string) {
        const stopWatcher = watch(
            () => route.query.error,
            (error) => {
                const errorCode = toText<ResponseCodes.Code>(error);
                if (!errorCode) {
                    return;
                }

                errorToast.handle(errorCode, {
                    title: toText(route.query.title),
                    description: toText(route.query.description),
                });

                clearQuery(path);
            },
            { immediate: true },
        );

        watchers.value.add(stopWatcher);
    }

    function on<T extends ResponseCodes.Code>(error: T, cb: RouteErrorHandler, path?: string) {
        onMap({ [error]: cb }, path);
    }

    onUnmounted(() => {
        watchers.value.forEach((watcher) => watcher());
        watchers.value.clear();
    });

    return {
        onMap,
        onToast,
        on,
    };
}
