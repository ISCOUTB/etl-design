import type { ShallowRef } from "vue";

export class TabsManager<C extends Component> {
    #loadedComponents: ShallowRef<Map<string, Components.TabsManager.LoadedComponent<C>>>;

    #activeTabValue: ShallowRef<string | null>;

    constructor(initialTabs: Components.TabsManager.TabDefinition<C>[]) {
        this.#loadedComponents = shallowRef(
            new Map<string, Components.TabsManager.LoadedComponent<C>>(),
        );

        this.#activeTabValue = shallowRef<string | null>(null);

        this.#preloadComponents(initialTabs);

        if (initialTabs.length > 0) {
            this.#activeTabValue.value = initialTabs[0]!.meta.value;
        }
    }

    async #preloadComponents(tabs: Components.TabsManager.TabDefinition<C>[]) {
        await Promise.all(tabs.map((tab) => this.#loadComponent(tab)));
    }

    async #loadComponent(tab: Components.TabsManager.TabDefinition<C>) {
        if (this.#loadedComponents.value.has(tab.meta.value)) {
            return;
        }

        const component = defineAsyncComponent({
            loader: tab.component,
        });

        this.#loadedComponents.value.set(tab.meta.value, {
            meta: tab.meta,
            props: tab.props,
            component: markRaw(component),
        });
    }

    async setActiveTab(tabValue: Components.TabsManager.TabMeta["value"]) {
        if (!this.#loadedComponents.value.has(tabValue)) {
            return;
        }

        const previousTab = this.#loadedComponents.value.get(tabValue)!;

        if (previousTab.meta.atomic) {
            this.#loadedComponents.value.delete(previousTab.meta.value);
        }

        this.#activeTabValue.value = tabValue;
    }

    async addTab(tab: Components.TabsManager.TabDefinition<C>, setActive = false) {
        await this.#loadComponent(tab);

        if (setActive) {
            this.#activeTabValue.value = tab.meta.value;
        }
    }

    get activeTabValue() {
        return readonly(this.#activeTabValue);
    }

    get tabs() {
        return computed(() => {
            return Array.from(this.#loadedComponents.value.values());
        });
    }

    get registry() {
        return readonly(this.#loadedComponents);
    }

    get component() {
        return computed(() => {
            if (!this.#activeTabValue.value) {
                return;
            }
            return this.#loadedComponents.value.get(this.#activeTabValue.value)?.component;
        });
    }

    get components() {
        return Array.from(this.#loadedComponents.value.values()).map((tab) => ({
            component: tab.component,
            props: tab.props,
            meta: tab.meta,
        }));
    }

    get props() {
        return computed(() => {
            if (!this.#activeTabValue.value) {
                return;
            }

            return this.#loadedComponents.value.get(this.#activeTabValue.value)?.props;
        });
    }
}
