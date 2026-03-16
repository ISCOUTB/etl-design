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
    const stateKey = options?.key ?? `use-tabs-manager:${route.path}`;
    const componentCache = shallowRef(new Map<TabMeta["value"], Raw<Component>>());

    const initial = computed(() => toValue(initialTabs));

    const tabs = shallowRef(
        new Map<TabMeta["value"], TabEntry>(initial.value.map((entry) => [entry.tab.value, entry])),
    );
    const filteredTabs = computed(() =>
        Array.from(tabs.value.values()).filter((entry) => !toValue(entry.tab.hidden)),
    );

    const firstTabValue = computed(() => filteredTabs.value[0]?.tab.value ?? "");

    const activeTab = useState<TabMeta["value"]>(`${stateKey}:active-tab`, () => {
        const candidate = options?.initialActive;
        if (candidate && filteredTabs.value.some((entry) => entry.tab.value === candidate)) {
            return candidate;
        }

        return firstTabValue.value;
    });
    const currentEntry = computed(() => {
        const found = filteredTabs.value.find((entry) => entry.tab.value === activeTab.value);
        if (found) {
            return found;
        }

        return filteredTabs.value[0];
    });

    const component = computed(() => {
        if (!currentEntry.value) {
            return;
        }

        return resolveComponent(currentEntry.value);
    });
    const props = computed(() => currentEntry.value?.props ?? {});

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
        const targetTab = filteredTabs.value.find((entry) => entry.tab.value === tabValue);
        if (!targetTab) {
            return;
        }

        const previous = filteredTabs.value.find((entry) => entry.tab.value === activeTab.value);
        activeTab.value = targetTab.tab.value;

        if (previous && toValue(previous.tab.atomic)) {
            removeTab(previous.tab.value);
        }
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
            tabs.value.values().map(async (entry) => {
                await entry.component();
                resolveComponent(entry);
            }),
        );
    }

    watch(
        initial,
        (nextInitial) => {
            const dynamicTabs = Array.from(tabs.value.values()).filter(
                (entry) =>
                    !nextInitial.some((baseEntry) => baseEntry.tab.value === entry.tab.value),
            );

            tabs.value = new Map([
                ...nextInitial.map((entry) => [entry.tab.value, entry] as [string, TabEntry]),
                ...dynamicTabs.map((entry) => [entry.tab.value, entry] as [string, TabEntry]),
            ]);
        },
        { immediate: true },
    );

    watch(
        filteredTabs,
        (visible) => {
            if (!visible.length) {
                activeTab.value = "";
                return;
            }

            const exists = visible.some((entry) => entry.tab.value === activeTab.value);
            if (!exists) {
                activeTab.value = visible[0]!.tab.value;
            }
        },
        { immediate: true },
    );

    if (options?.model) {
        syncRef(options.model, activeTab, { direction: "ltr", immediate: true });
    }

    return {
        tabs: readonly(tabs),
        filteredTabs: readonly(filteredTabs),
        component: readonly(component),
        props: readonly(props),
        activeTab: readonly(activeTab),
        dispatch: {
            preload,
            setActive,
            addTab,
            removeTab,
        },
    };
}
