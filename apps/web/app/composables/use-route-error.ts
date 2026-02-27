import type { WatchStopHandle } from "vue";

interface Args {
    title: string;
    description: string;
}

export default function () {
    const watchers = useState<Set<WatchStopHandle>>(
        "use-route-error:watchers",
        () => new Set<WatchStopHandle>(),
    );

    const route = useRoute();

    function on<T extends ResponseCodes.Code>(
        error: T,
        cb: (args: Partial<Args>) => unknown,
        path?: string,
    ) {
        const stopWatcher = watch(
            () => route.query.error,
            (generatedError) => {
                if ((generatedError as T) !== error) {
                    return;
                }

                const query = new Map(Object.entries(route.query));
                query.delete("error");

                const targetPath = path ?? route.path;

                cb({
                    title: query.get("title")?.toString(),
                    description: query.get("description")?.toString(),
                });

                navigateTo({
                    path: targetPath,
                    query: Object.fromEntries(query),
                });
            },
            { immediate: true },
        );

        watchers.value.add(stopWatcher);
    }

    onUnmounted(() => {
        watchers.value.forEach((watcher) => watcher());
        watchers.value.clear();
    });

    return {
        on,
    };
}
