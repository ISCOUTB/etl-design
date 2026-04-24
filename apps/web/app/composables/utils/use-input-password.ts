type InputType = "password" | "text";

interface Options {
    key?: string;
    id?: MaybeRefOrGetter<string | undefined>;
}

export default function (initial: InputType = "password", options?: Options) {
    const KEY = options?.key ?? NuxtKeys.Components.InputPassword();

    const type = useState(KEY, () => initial);
    const id = computed(() => toValue(options?.id));

    function toggle() {
        if (type.value === "password") {
            type.value = "text";
            return;
        }

        if (type.value === "text") {
            type.value = "password";
        }
    }

    async function onToggle() {
        toggle();

        await nextTick();

        if (!id.value) {
            return;
        }

        const element = document.getElementById(id.value);
        if (!(element instanceof HTMLInputElement)) {
            return;
        }

        const length = element.value.length;
        element.focus();
        element.setSelectionRange(length, length);
    }

    return {
        type,
        dispatch: {
            toggle,
            onToggle,
        },
    };
}
