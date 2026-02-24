<script setup lang="ts" generic="TData, TValue">
    import type {
        ColumnDef,
        ColumnFiltersState,
        SortingState,
        VisibilityState,
    } from "@tanstack/vue-table";
    import {
        FlexRender,
        getCoreRowModel,
        getFilteredRowModel,
        getPaginationRowModel,
        getSortedRowModel,
        useVueTable,
    } from "@tanstack/vue-table";

    interface Props<Data, Value> {
        stateKey: string;
        columns: MaybeRefOrGetter<ColumnDef<Data, Value>[]>;
        data: MaybeRefOrGetter<Data[]>;
    }

    const props = defineProps<Props<TData, TValue>>();

    const data = computed(() => toValue(props.data));
    const columns = computed(() => toValue(props.columns));

    const sorting = useState<SortingState>(`${props.stateKey}-sorting-state`, () => []);
    const columnFilters = useState<ColumnFiltersState>(
        `${props.stateKey}-column-filters`,
        () => [],
    );
    const columnVisibility = useState<VisibilityState>(
        `${props.stateKey}-column-visibility`,
        () => ({}),
    );

    const table = useVueTable({
        get data() {
            return data.value;
        },
        get columns() {
            return columns.value;
        },
        state: {
            get sorting() {
                return sorting.value;
            },
            get columnFilters() {
                return columnFilters.value;
            },
            get columnVisibility() {
                return columnVisibility.value;
            },
        },
        onSortingChange: (updaterOrValue) => {
            if (typeof updaterOrValue === "function") {
                sorting.value = updaterOrValue(sorting.value);
                return;
            }

            sorting.value = updaterOrValue;
        },
        onColumnFiltersChange: (updaterOrValue) => {
            if (typeof updaterOrValue === "function") {
                columnFilters.value = updaterOrValue(columnFilters.value);
                return;
            }

            columnFilters.value = updaterOrValue;
        },
        onColumnVisibilityChange: (updaterOrValue) => {
            if (typeof updaterOrValue === "function") {
                columnVisibility.value = updaterOrValue(columnVisibility.value);
                return;
            }

            columnVisibility.value = updaterOrValue;
        },
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
    });

    defineExpose({ table });
</script>

<template>
    <!-- Maybe we could expose table object in a better way :S -->
    <div class="space-y-4">
        <slot name="default" :table="table">
            <slot name="search-input" />

            <div class="overflow-hidden rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow
                            v-for="headerGroup in table.getHeaderGroups()"
                            :key="headerGroup.id"
                        >
                            <TableHead v-for="header in headerGroup.headers" :key="header.id">
                                <template v-if="!header.isPlaceholder">
                                    <FlexRender
                                        :render="header.column.columnDef.header"
                                        :props="header.getContext()"
                                    />
                                </template>
                            </TableHead>
                        </TableRow>
                    </TableHeader>

                    <TableBody>
                        <template v-if="table.getRowModel().rows.length">
                            <TableRow
                                v-for="row in table.getRowModel().rows"
                                :key="row.id"
                                :data-state="row.getIsSelected() && 'selected'"
                            >
                                <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                                    <FlexRender
                                        :render="cell.column.columnDef.cell"
                                        :props="cell.getContext()"
                                    />
                                </TableCell>
                            </TableRow>
                        </template>
                        <template v-else>
                            <TableRow>
                                <TableCell :colspan="columns.length" class="h-24 text-center">
                                    <slot name="no-results" />
                                </TableCell>
                            </TableRow>
                        </template>
                    </TableBody>
                </Table>
            </div>
            <div class="flex items-center justify-between">
                <slot name="total-elements">
                    <div />
                </slot>

                <div class="space-x-2">
                    <Button
                        variant="outline"
                        size="sm"
                        :disabled="!table.getCanPreviousPage()"
                        @click="table.previousPage()"
                    >
                        <slot name="control-previous" />
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        :disabled="!table.getCanNextPage()"
                        @click="table.nextPage()"
                    >
                        <slot name="control-next" />
                    </Button>
                </div>
            </div>
        </slot>
    </div>
</template>
