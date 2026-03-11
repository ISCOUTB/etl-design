<script setup lang="ts" generic="TData">
    import { useDataTableContext } from "@/components/common/data-table/utils";

    const context = useDataTableContext<TData>();
</script>

<template>
    <TableHeader>
        <TableRow>
            <TableHead v-for="column in context.columns.value" :key="column.key">
                <span>
                    <template v-if="$te(column.label)">
                        {{ $t(column.label) }}
                    </template>
                    <template v-else>
                        {{ column.label }}
                    </template>
                </span>

                <slot
                    :name="`header-${column.key.toString()}`"
                    v-bind="{ toggleSorting: context.toggleSorting }"
                />
            </TableHead>
        </TableRow>
    </TableHeader>
</template>
