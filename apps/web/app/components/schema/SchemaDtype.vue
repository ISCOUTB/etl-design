<script setup lang="ts">
    import { cn } from "~/lib/utils";

    interface Props {
        dtype: Dtype;
    }

    defineProps<Props>();
</script>

<template>
    <div class="flex items-center space-x-2">
        <template v-if="$slots.icon">
            <div
                :class="
                    cn(
                        'flex size-6 items-center justify-center rounded',
                        TableUtils.getColor(dtype),
                    )
                "
            >
                <slot name="icon" />
            </div>
        </template>
        <div>
            <slot />
        </div>
    </div>
</template>
