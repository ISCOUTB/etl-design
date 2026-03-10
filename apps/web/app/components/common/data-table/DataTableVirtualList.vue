<script setup lang="ts" generic="TData">
    import { provideDataTableItemsContext, useDataTableContext } from "./utils";

    interface Props {
        rowHeight?: number;
        overscan?: number;
    }

    const props = withDefaults(defineProps<Props>(), {
        rowHeight: 44,
        overscan: 8,
    });

    const context = useDataTableContext<TData>();

    const { list, containerProps, scrollTo } = useVirtualList(context.sortedData, {
        itemHeight: props.rowHeight,
        overscan: props.overscan,
    });

    const items = computed(() => list.value.map((item) => item.data));

    const startIndex = computed(() => list.value[0]?.index ?? 0);
    const endIndex = computed(() => list.value[list.value.length - 1]?.index ?? -1);
    const topSpacerHeight = computed(() => startIndex.value * props.rowHeight);
    const bottomSpacerHeight = computed(() => {
        const total = context.sortedData.value.length;
        if (endIndex.value < 0) {
            return 0;
        }

        return Math.max(0, (total - endIndex.value) * props.rowHeight);
    });

    provideDataTableItemsContext(items);

    watchEffect(() => {
        const element = context.container.value;
        if (!element) {
            return;
        }

        containerProps.ref.value = element;
        element.onscroll = containerProps.onScroll;
    });

    onMounted(() => {
        containerProps.onScroll();
    });
</script>

<template>
    <TableRow v-if="topSpacerHeight > 0" aria-hidden="true">
        <TableCell
            :colspan="context.columns.length"
            class="h-0 border-0 p-0"
            :style="{ height: `${topSpacerHeight}px` }"
        />
    </TableRow>

    <slot v-bind="{ items, scrollTo }" />

    <TableRow v-if="bottomSpacerHeight > 0" aria-hidden="true">
        <TableCell
            :colspan="context.columns.length"
            class="h-0 border-0 p-0"
            :style="{ height: `${bottomSpacerHeight}px` }"
        />
    </TableRow>
</template>
