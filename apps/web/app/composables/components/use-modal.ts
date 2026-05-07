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

    const state = useState<Components.Modal.State>("modal:state", () => ({
        currentModalKey: undefined,
        currentKind: "sheet",
        open: false,
        componentProps: {},
        containerProps: {},
    }));

    const currentComponent = computed(() => {
        return (
            componentRegistry.value.find(
                (component) => component.key === state.value.currentModalKey,
            )?.component ?? null
        );
    });

    function loadComponent<C extends Component, Args extends Components.Modal.Args<C>>(
        args: MaybeRefOrGetter<Args>,
        options: LoadComponentOptions = { autoOpen: true },
    ) {
        const { key, loader, kind = "sheet", props, containerProps } = toValue(args);

        const existingEntry = componentRegistry.value.find((component) => component.key === key);

        if (existingEntry) {
            setState({ currentModalKey: key, currentKind: kind, componentProps: props as object });

            if (options.autoOpen) {
                setOpen(true);
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

        setState({
            currentModalKey: key,
            currentKind: kind,
            componentProps: props,
            containerProps,
        });

        if (options.autoOpen) {
            setOpen(true);
        }
    }

    function setOpen(open: boolean) {
        state.value = { ...state.value, open };
    }

    function setState(patch: Partial<Components.Modal.State>) {
        state.value = { ...state.value, ...patch };
    }

    function setModalKind(patch: Components.Modal.Kind) {
        state.value = { ...state.value, currentKind: patch };
    }

    return {
        state,
        currentComponent,
        dispatch: {
            setOpen,
            setModalKind,
            loadComponent,
        },
    };
}
