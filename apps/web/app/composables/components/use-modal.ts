interface ModalComponent {
    key: string;
    component: Component;
}

interface LoadComponentOptions {
    autoOpen: boolean;
}

const componentRegistry = shallowRef<ModalComponent[]>([]);

export default function () {
    const config = useAppConfig();

    const currentModalKey = useState<string | undefined>("modal:current-component:key");
    const open = useState("modal:open", () => false);
    const componentProps = useState<object>("modal:component-props");

    const currentComponent = computed(() => {
        return (
            componentRegistry.value.find((component) => component.key === currentModalKey.value)
                ?.component ?? null
        );
    });

    function loadComponent<C extends Component>(
        { loader, props, key }: Components.Modal.Args<C>,
        options: LoadComponentOptions = { autoOpen: true },
    ) {
        const existingEntry = componentRegistry.value.find((component) => component.key === key);

        if (existingEntry) {
            currentModalKey.value = key;
            componentProps.value = props as object;

            if (options.autoOpen) {
                open.value = true;
            }

            return;
        }

        const component = defineAsyncComponent({
            loader,
            delay: 0,
            timeout: 5000,
        });

        if (componentRegistry.value.length >= config.composables.useModal.maxStorageLength) {
            componentRegistry.value.shift();
        }

        componentRegistry.value = [
            ...componentRegistry.value,
            { key, component: markRaw(component) },
        ];

        currentModalKey.value = key;
        componentProps.value = props as object;

        if (options.autoOpen) {
            open.value = true;
        }
    }

    return {
        componentProps,
        currentModalKey: readonly(currentModalKey),
        currentComponent,
        loadComponent,
        open,
    };
}
