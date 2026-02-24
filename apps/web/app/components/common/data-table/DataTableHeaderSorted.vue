<script setup lang="ts" generic="TData = unknown, TValue = unknown">
    import type { Column } from "@tanstack/vue-table";
    import { ArrowUpDown } from "lucide-vue-next";

    interface Props<Data, Value> {
        title: string;
        column: Column<Data, Value>;
    }

    defineProps<Props<TData, TValue>>();
</script>

<template>
    <Button
        variant="ghost"
        size="sm"
        class="-ml-3 h-8 data-[state=open]:bg-accent"
        @click="column.toggleSorting(column.getIsSorted() === 'asc')"
    >
        <span>{{ title }}</span>
        <slot name="icon">
            <ArrowUpDown class="ml-2 h-4 w-4" />
        </slot>
    </Button>
</template>
