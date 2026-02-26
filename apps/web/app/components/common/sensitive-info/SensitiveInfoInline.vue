<script setup lang="ts">
    import { Dot } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

    interface Props {
        value: MaybeRefOrGetter<string>;
        maskChar?: string;
    }

    const props = withDefaults(defineProps<Props>(), { maskChar: "\u2022" });

    const [visible, toggleVisible] = useToggle();

    const value = computed(() => toValue(props.value));
    const displayValue = computed(() => {
        if (visible.value) {
            return value.value;
        }

        return props.maskChar.repeat(Math.max(value.value.length, 8));
    });
</script>

<template>
    <TooltipProvider>
        <Tooltip :delay-duration="500">
            <TooltipTrigger>
                <span
                    class="font-mono text-sm transition-all duration-300 select-none cursor-pointer flex items-center"
                    :class="cn(!visible && 'blur-sm')"
                    aria-live="polite"
                    @click="() => toggleVisible()"
                >
                    {{ displayValue }}
                    <Dot v-if="visible" class="text-green-500 size-5" />
                </span>
            </TooltipTrigger>
            <TooltipContent side="right">
                {{ $t("common.visibility.toggle") }}
            </TooltipContent>
        </Tooltip>
    </TooltipProvider>
</template>
