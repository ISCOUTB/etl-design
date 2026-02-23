<script setup lang="ts">
    interface Props {
        item: Components.GenericDropdown.Item;
    }

    defineProps<Props>();
</script>

<template>
    <template v-if="item.to">
        <NuxtLink :to="item.to()">
            <component :is="item.icon" class="mr-2 h-4 w-4" />
            <span>{{ $t(item.label) }}</span>
        </NuxtLink>
    </template>
    <template v-else>
        <component :is="item.icon" class="mr-2 h-4 w-4" />
        <span>{{ $t(item.label) }}</span>
    </template>
</template>
