/* eslint-disable style/type-generic-spacing */
import type { Component, Raw } from "vue";

interface TabMeta {
    label: string;
    value: string;
    atomic?: boolean | (() => boolean);
    icon?: Components.LucideIconComponent;
}

interface TabEntry<C extends Component = Component> {
    tab: TabMeta;
    component: Components.ComponentLoader<C>;
    props: Components.ComponentProps<C>;
}

interface UseTabsManagerOptions {
    key?: string;
    initialActive?: string;
    model: Ref<string>;
}

export default function <C extends Component>(
    initialTabs: MaybeRefOrGetter<[TabEntry<C>, ...TabEntry<C>[]]>,
    options?: UseTabsManagerOptions,
) {
    const route = useRoute();
    const initial = toValue(initialTabs);

    const tabs = shallowRef(new Map(initial.map((entry) => [entry.tab.value, entry])));
    const firstTabValue = initial[0].tab.value;

    const stateKey = options?.key ?? `use-tabs-manager:${route.path}`;
    const activeTab = useState<string>(stateKey, () => {
        const candidate = options?.initialActive;
        if (candidate && tabs.value.has(candidate)) {
            return candidate;
        }

        return firstTabValue;
    });

    const componentCache = shallowRef(new Map<TabMeta["value"], Raw<C>>());

    const currentEntry = computed(() => {
        const found = tabs.value.get(activeTab.value);
        if (found) {
            return found;
        }

        const fallback =
            tabs.value.get(firstTabValue) ?? ([...tabs.value.values()][0] as TabEntry<C>);
        if (fallback) {
            activeTab.value = fallback?.tab.value;
        }

        return fallback;
    });

    const component = computed(() => {
        const entry = currentEntry.value;
        const key = entry.tab.value;

        const cached = componentCache.value.get(key);
        if (cached) {
            return cached;
        }

        const wrapped = markRaw(
            defineAsyncComponent({ loader: entry.component, delay: 0, timeout: 5000 }),
        );

        componentCache.value.set(key, wrapped);

        return wrapped;
    });

    const props = computed(() => currentEntry.value.props);

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
            tabs.value.delete(previous.tab.value);
        }
    }

    onMounted(() => {
        if (options?.model) {
            syncRef(options.model, activeTab);
        }
    });

    return {
        tabs: readonly(tabs),
        component: readonly(component),
        props: readonly(props),
        activeTab: readonly(activeTab),
        setActive,
    };
}
