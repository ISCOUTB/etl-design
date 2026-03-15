import type { Component, Raw } from "vue";

export interface TabMeta {
    label: string;
    value: string;
    hidden?: boolean | (() => boolean);
    atomic?: boolean | (() => boolean);
    icon?: Components.LucideIconComponent;
    class?: string | string[] | Record<string, boolean>;
}

export interface TabEntry {
    tab: TabMeta;
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
    initialTabs: MaybeRefOrGetter<[TabEntry, ...TabEntry[]]>,
    options?: UseTabsManagerOptions,
) {
    const route = useRoute();
    const initial = toValue(initialTabs);
    const filteredTabs = computed(() => filterTabs(initial));

    const tabs = shallowRef(new Map(filteredTabs.value.map((entry) => [entry.tab.value, entry])));
    const firstTabValue = computed(() => filteredTabs.value[0]?.tab.value ?? initial[0].tab.value);

    const stateKey = options?.key ?? `use-tabs-manager:${route.path}`;
    const activeTab = useState<string>(stateKey, () => {
        const candidate = options?.initialActive;
        if (candidate && tabs.value.has(candidate)) {
            return candidate;
        }

        return firstTabValue.value;
    });

    const componentCache = shallowRef(new Map<TabMeta["value"], Raw<Component>>());

    const currentEntry = computed(() => {
        const found = tabs.value.get(activeTab.value);
        if (found) {
            return found;
        }

        return tabs.value.get(firstTabValue.value) ?? ([...tabs.value.values()][0] as TabEntry);
    });

    const component = computed(() => resolveComponent(currentEntry.value));
    const props = computed(() => currentEntry.value.props);

    function addTab(entry: TabEntry) {
        const next = new Map(tabs.value);
        next.set(entry.tab.value, entry);
        tabs.value = next;
    }

    function removeTab(value: TabMeta["value"]) {
        const next = new Map(tabs.value);
        next.delete(value);
        tabs.value = next;
    }

    function setActive(tabValue: TabMeta["value"]) {
        const targetTab = tabs.value.get(tabValue);
        if (!targetTab) {
            return;
        }

        const previous = tabs.value.get(activeTab.value);
        if (!previous) {
            return;
        }

        activeTab.value = targetTab.tab.value;

        const atomic = toValue(previous.tab.atomic);
        if (atomic) {
            removeTab(previous.tab.value);
        }
    }

    function filterTabs(tabs: [TabEntry, ...TabEntry[]]) {
        return tabs.filter((entry) => !toValue(entry.tab.hidden));
    }

    function resolveComponent(entry: TabEntry) {
        const key = entry.tab.value;

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

    async function preload(values?: TabMeta["value"][]) {
        if (values?.length) {
            const entries = values
                .map((value) => tabs.value.get(value))
                .filter((entry): entry is TabEntry => !!entry);

            await Promise.all(
                entries.map(async (entry) => {
                    await entry.component();
                    resolveComponent(entry);
                }),
            );
            return;
        }

        await Promise.all(
            [...tabs.value.values()].map(async (entry) => {
                await entry.component();
                resolveComponent(entry);
            }),
        );
    }

    function preloadTabs(values?: TabMeta["value"][]) {
        return preload(values);
    }

    watch(
        currentEntry,
        (entry) => {
            if (entry && entry.tab.value !== activeTab.value) {
                activeTab.value = entry.tab.value;
            }
        },
        { immediate: true },
    );

    onMounted(() => {
        if (options?.model) {
            syncRef(options.model, activeTab, { direction: "ltr" });
        }
    });

    return {
        tabs: readonly(tabs),
        component: readonly(component),
        props: readonly(props),
        activeTab: readonly(activeTab),
        dispatch: {
            setActive,
            addTab,
            removeTab,
            preload,
            preloadTabs,
        },
    };
}
