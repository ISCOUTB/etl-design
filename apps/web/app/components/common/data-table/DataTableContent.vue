<script setup lang="ts" generic="TData">
    import { useDataTableContext, useDataTableItemsContext } from "./utils";

    interface Props<T> {
        items?: T[];
    }

    const props = defineProps<Props<TData>>();

    const context = useDataTableContext<TData>();
    const contextItems = useDataTableItemsContext<TData>();

    const rows = computed(() => props.items ?? contextItems.value);
</script>

<template>
    <template v-for="row in rows" :key="String(row[context.index])">
        <TableRow>
            <TableCell v-for="column in context.columns" :key="String(column.key)">
                <slot
                    :name="`cell-${column.key.toString()}`"
                    v-bind="{ row, value: row[column.key as keyof TData], column }"
                >
                    {{ row[column.key as keyof TData] }}
                </slot>
            </TableCell>
        </TableRow>
    </template>
</template>
