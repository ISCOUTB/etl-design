<script setup lang="ts">
    import type { HTMLAttributes, InputHTMLAttributes } from "vue";
    import { Eye, EyeOff } from "lucide-vue-next";

    interface Props {
        defaultValue?: string | number;
        modelValue?: string | number;
        class?: HTMLAttributes["class"];
    }

    defineOptions({ inheritAttrs: false });
    const props = defineProps<Props>();
    const emits = defineEmits<{
        (e: "update:modelValue", payload: string | number): void;
    }>();

    const input = useTemplateRef("input");
    const modelValue = useVModel(props, "modelValue", emits, {
        passive: true,
        defaultValue: props.defaultValue,
    });
    const [status, toggle] = useToggle(true);
    const type = computed<InputHTMLAttributes["type"]>(() => {
        if (status.value) {
            return "password";
        }

        return "text";
    });

    async function onToggle() {
        toggle();

        await nextTick();

        const element: HTMLElement | undefined = input.value?.$el;
        if (!element) {
            return;
        }

        if (element instanceof HTMLInputElement) {
            const length = element.value.length;
            element.focus();
            element.setSelectionRange(length, length);
        }
    }
</script>

<template>
    <InputGroup>
        <InputGroupInput
            v-bind="$attrs"
            ref="input"
            v-model="modelValue"
            :class="props.class"
            :type="type"
        />
        <InputGroupAddon class="gap-1" align="inline-end">
            <InputGroupButton type="button" @click="onToggle">
                <template v-if="status">
                    <Eye />
                </template>
                <template v-else>
                    <EyeOff />
                </template>
            </InputGroupButton>
        </InputGroupAddon>
    </InputGroup>
</template>
