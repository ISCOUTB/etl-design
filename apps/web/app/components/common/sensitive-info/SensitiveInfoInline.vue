<script setup lang="ts">
    import type { HTMLAttributes } from "vue";
    import { Dot } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

    interface Props {
        value: MaybeRefOrGetter<string>;
        class?: HTMLAttributes["class"];
        maskChar?: string;
        timeout?: number;
    }

    defineOptions({ inheritAttrs: false });

    const props = withDefaults(defineProps<Props>(), { maskChar: "\u2022", timeout: 3000 });

    const [visible, toggleVisible] = useToggle();

    const value = computed(() => toValue(props.value));
    const displayValue = computed(() => {
        if (visible.value) {
            return value.value;
        }

        return props.maskChar.repeat(Math.max(value.value.length, 8));
    });

    const { start, stop } = useTimeoutFn(
        () => {
            visible.value = false;
        },
        props.timeout,
        { immediate: true },
    );

    function toggle() {
        const value = toggleVisible();
        if (value) {
            start();
            return;
        }

        stop();
    }
</script>

<template>
    <TooltipProvider>
        <Tooltip :delay-duration="500">
            <TooltipTrigger>
                <span
                    :class="
                        cn(
                            'font-mono text-sm transition-all duration-300 select-none cursor-pointer flex items-center',
                            !visible && 'blur-sm',
                            props.class,
                        )
                    "
                    aria-live="polite"
                    @click="() => toggle()"
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
