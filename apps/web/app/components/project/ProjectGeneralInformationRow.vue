<script setup lang="ts">
    import type { HTMLAttributes } from "vue";
    import { Copy, TriangleAlert } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

    interface Props {
        icon: Components.LucideIconComponent;
        label: string;
        value: MaybeRefOrGetter<string | undefined | null>;
        class?: HTMLAttributes["class"];
        copyable?: boolean;
        noWarning?: boolean;
        noSensitive?: boolean;
    }

    const props = withDefaults(defineProps<Props>(), {
        copyable: false,
    });

    const value = computed(() => toValue(props.value));
    const clipboard = useClipboard();
</script>

<template>
    <div class="flex items-center justify-between py-3">
        <div class="flex items-center space-x-3 text-muted-foreground">
            <component :is="icon" class="size-4 shrink-0" />
            <span v-if="$te(label)" class="text-sm">{{ $t(label) }}</span>
            <span v-else class="text-sm">{{ label }}</span>
        </div>
        <div class="flex items-center space-x-2">
            <template v-if="value && value.length > 0">
                <span :class="cn('text-sm text-foreground', props.class)">
                    <template v-if="noSensitive">
                        {{ value }}
                    </template>
                    <template v-else>
                        <SensitiveInfoInline :value="value" />
                    </template>
                </span>

                <Button
                    v-if="copyable"
                    variant="ghost"
                    size="icon"
                    class="size-8"
                    @click="
                        () => {
                            if (value) {
                                clipboard.copy(value);
                            }
                        }
                    "
                >
                    <Copy />
                    <span class="sr-only">Copy ID</span>
                </Button>
            </template>

            <template v-if="!value && !noWarning">
                <TriangleAlert class="size-6 text-yellow-500/50 dark:text-orange-500/60" />
            </template>
        </div>
    </div>
</template>
