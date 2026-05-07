<script setup lang="ts">
    import { cn } from "~/lib/utils";

    interface Props {
        loading: MaybeRefOrGetter<boolean>;
    }

    defineOptions({ inheritAttrs: false });
    const props = defineProps<Props>();
    const loading = computed(() => toValue(props.loading));
</script>

<template>
    <template v-if="loading">
        <slot name="loader">
            <Spinner :class="cn($attrs.class)" />
        </slot>
    </template>
    <template v-else>
        <slot />
    </template>
</template>
