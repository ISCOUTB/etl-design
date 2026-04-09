<script setup lang="ts">
    import type { HTMLAttributes } from "vue";
    import { useVModel } from "@vueuse/core";
    import { Input } from "@/components/ui/input";
    import { cn } from "@/lib/utils";

    const props = defineProps<{
        defaultValue?: string | number;
        modelValue?: string | number;
        class?: HTMLAttributes["class"];
    }>();

    const emits = defineEmits<{
        (e: "update:modelValue", payload: string | number): void;
    }>();

    const modelValue = useVModel(props, "modelValue", emits, {
        passive: true,
        defaultValue: props.defaultValue,
    });
</script>

<template>
    <Input
        v-model="modelValue"
        data-slot="input-group-control"
        :class="
            cn(
                'flex-1 rounded-none border-0 bg-transparent shadow-none focus-visible:ring-0 dark:bg-transparent',
                props.class,
            )
        "
    />
</template>
