<script setup lang="ts">
    import type { HTMLAttributes } from "vue";
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
    const attrs = useAttrs();

    const modelValue = useVModel(props, "modelValue", emits, {
        passive: true,
        defaultValue: props.defaultValue,
    });

    const manager = useInputPassword("password", { id: () => String(attrs.id) });
</script>

<template>
    <InputGroup>
        <InputGroupInput
            v-bind="$attrs"
            v-model="modelValue"
            :class="props.class"
            :type="manager.type.value"
        />
        <InputGroupAddon align="inline-end">
            <InputGroupButton @click="manager.dispatch.onToggle">
                <template v-if="manager.type.value === 'password'">
                    <Eye />
                </template>
                <template v-if="manager.type.value === 'text'">
                    <EyeOff />
                </template>
            </InputGroupButton>
        </InputGroupAddon>
    </InputGroup>
</template>
