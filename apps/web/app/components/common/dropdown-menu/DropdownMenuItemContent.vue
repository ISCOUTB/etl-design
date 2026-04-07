<script setup lang="ts" generic="TContext">
    interface Props<T> {
        item: Components.GenericDropdown.Item<T>;
        context?: MaybeRefOrGetter<T>;
    }

    const props = defineProps<Props<TContext>>();
    const context = computed(() => toValue(props.context));
</script>

<template>
    <template v-if="item.to">
        <NuxtLink :to="item.to(context)">
            <component :is="item.icon" class="mr-2 h-4 w-4" />
            <span>{{ $t(item.label) }}</span>
        </NuxtLink>
    </template>
    <template v-else>
        <component :is="item.icon" class="mr-2 h-4 w-4" />
        <span>{{ $t(item.label) }}</span>
    </template>
</template>
