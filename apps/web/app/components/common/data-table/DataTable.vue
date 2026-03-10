<script setup lang="ts" generic="TData">
    import type { HtmlHTMLAttributes } from "vue";
    import type { Column, SortingState } from "@/components/common/data-table/utils";
    import { provideDataTableContext } from "@/components/common/data-table/utils";
    import { cn } from "~/lib/utils";

    interface Props<T> {
        index: keyof T;
        columns: Column<T>[];
        data: MaybeRefOrGetter<T[] | undefined>;
        pageSize?: number;
        compareFn?: (sorting: SortingState<T>) => (a: T, b: T) => number;
        class?: HtmlHTMLAttributes["class"];
    }

    const props = withDefaults(defineProps<Props<TData>>(), {
        pageSize: 10,
        compareFn: (sorting: SortingState<TData>) => (a: TData, b: TData) => {
            const av = a[sorting.key];
            const bv = b[sorting.key];

            if (av < bv) {
                if (sorting.direction === "asc") {
                    return -1;
                }

                return 1;
            }

            if (av > bv) {
                if (sorting.direction === "asc") {
                    return 1;
                }

                return -1;
            }

            return 0;
        },
    });

    const route = useRoute();
    const data = computed(() => toValue(props.data) ?? []);
    const sorting = useState<SortingState<TData>>(
        NuxtKeys.Components.DataTable.Sorting(route.path),
        () => ({ key: props.index, direction: "asc" }),
    );
    const sortedData = computed(() => data.value.toSorted(props.compareFn(sorting.value)));

    function toggleSorting(key: keyof TData) {
        if (sorting.value.key !== key) {
            sorting.value = { key, direction: "asc" };
            return;
        }

        if (sorting.value.direction === "asc") {
            sorting.value = {
                key,
                direction: "desc",
            };
            return;
        }

        if (sorting.value.direction === "desc") {
            sorting.value = {
                key,
                direction: "asc",
            };
        }
    }

    const container = useTemplateRef("container");

    provideDataTableContext<TData>({
        index: props.index,
        columns: props.columns,
        data,
        sortedData,
        sorting,
        toggleSorting,
        pageSize: props.pageSize,
        container,
    });
</script>

<template>
    <div ref="container" :class="cn('overflow-auto', props.class)">
        <Table>
            <slot />
        </Table>
    </div>
</template>
