import type { Component, Raw } from "vue";

export interface Meta {
    label: string;
    value: string;
    hidden?: boolean | (() => boolean);
    atomic?: boolean | (() => boolean);
    icon?: Components.LucideIconComponent;
    class?: string | string[] | Record<string, boolean>;
}

export interface Entry {
    meta: Meta;
    component: Components.ComponentLoader<Component>;
    loadingComponent?: Component;
    props: Record<string, unknown>;
}

export interface UseTabsManagerOptions {
    key?: string;
    initialActive?: string;
    model: Ref<string>;
}

export default function (
    initialViews: MaybeRefOrGetter<[Entry, ...Entry[]]>,
    options?: UseTabsManagerOptions,
) {
    const route = useRoute();
    const stateKey = options?.key ?? `use-view-manager:${route.path}`;
    const componentCache = shallowRef(new Map<Meta["value"], Raw<Component>>());

    const initial = computed(() => toValue(initialViews));

    const views = shallowRef(
        new Map<Meta["value"], Entry>(initial.value.map((entry) => [entry.meta.value, entry])),
    );
    const filteredViews = computed(() =>
        Array.from(views.value.values()).filter((entry) => !toValue(entry.meta.hidden)),
    );

    const firstViewValue = computed(() => filteredViews.value[0]?.meta.value ?? "");

    const activeView = useState<Meta["value"]>(`${stateKey}:active-active-view`, () => {
        const candidate = options?.initialActive;
        if (candidate && filteredViews.value.some((entry) => entry.meta.value === candidate)) {
            return candidate;
        }

        return firstViewValue.value;
    });
    const currentView = computed(() => {
        const found = filteredViews.value.find((entry) => entry.meta.value === activeView.value);
        if (found) {
            return found;
        }

        return filteredViews.value[0];
    });

    const component = computed(() => {
        if (!currentView.value) {
            return;
        }

        return resolveComponent(currentView.value);
    });
    const props = computed(() => currentView.value?.props ?? {});

    function addView(entry: Entry) {
        const next = new Map(views.value);
        next.set(entry.meta.value, entry);
        views.value = next;
    }

    function removeView(value: Meta["value"]) {
        const next = new Map(views.value);
        next.delete(value);
        views.value = next;
    }

    function setActive(tabValue: Meta["value"]) {
        const targetView = filteredViews.value.find((entry) => entry.meta.value === tabValue);
        if (!targetView) {
            return;
        }

        const previous = filteredViews.value.find((entry) => entry.meta.value === activeView.value);
        activeView.value = targetView.meta.value;

        if (previous && toValue(previous.meta.atomic)) {
            removeView(previous.meta.value);
        }
    }

    function resolveComponent(entry: Entry) {
        const key = entry.meta.value;

        const cached = componentCache.value.get(key);
        if (cached) {
            return cached;
        }

        const wrapped = markRaw(
            defineAsyncComponent({
                loader: entry.component,
                delay: 0,
                timeout: 10_000,
                loadingComponent: entry.loadingComponent,
            }),
        );
        componentCache.value.set(key, wrapped);

        return wrapped;
    }

    async function preload(values?: Meta["value"][]) {
        if (values?.length) {
            const entries = values
                .map((value) => views.value.get(value))
                .filter((entry): entry is Entry => !!entry);

            await Promise.all(
                entries.map(async (entry) => {
                    await entry.component();
                    resolveComponent(entry);
                }),
            );
            return;
        }

        await Promise.all(
            views.value.values().map(async (entry) => {
                await entry.component();
                resolveComponent(entry);
            }),
        );
    }

    watch(
        initial,
        (nextInitial) => {
            const dynamicTabs = Array.from(views.value.values()).filter(
                (entry) =>
                    !nextInitial.some((baseEntry) => baseEntry.meta.value === entry.meta.value),
            );

            views.value = new Map([
                ...nextInitial.map((entry) => [entry.meta.value, entry] as [string, Entry]),
                ...dynamicTabs.map((entry) => [entry.meta.value, entry] as [string, Entry]),
            ]);
        },
        { immediate: true },
    );

    watch(
        filteredViews,
        (visible) => {
            if (!visible.length) {
                activeView.value = "";
                return;
            }

            const exists = visible.some((entry) => entry.meta.value === activeView.value);
            if (!exists) {
                activeView.value = visible[0]!.meta.value;
            }
        },
        { immediate: true },
    );

    if (options?.model) {
        syncRef(options.model, activeView, { immediate: true });
    }

    return {
        state: {
            views: readonly(views),
            activeView: readonly(activeView),
        },
        computed: {
            filteredViews: readonly(filteredViews),
            component: readonly(component),
            props: readonly(props),
        },
        dispatch: {
            addView,
            removeView,
            setActive,
            preload,
        },
    };
}
