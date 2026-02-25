<script setup lang="ts" generic="TData">
    interface Props {
        items: MaybeRefOrGetter<TData[] | undefined>;
        index: keyof TData;
        page: MaybeRefOrGetter<number>;
        pageSize: number;
        totalPages: MaybeRefOrGetter<number>;
        loading?: MaybeRefOrGetter<boolean>;
        url?: {
            queryParam: string;
            delayOnMount?: number;
        };
    }

    interface Emits {
        loadPage: [page: number];
    }

    type PaginationItem = { type: "item"; page: number } | { type: "ellipsis" };

    defineOptions({ inheritAttrs: false });

    const props = withDefaults(defineProps<Props>(), {
        loading: false,
        url: () => ({ queryParam: "page", delayOnMount: 0 }),
    });

    const emit = defineEmits<Emits>();

    const items = computed(() => toValue(props.items));
    const loading = computed(() => toValue(props.loading));
    const page = computed(() => toValue(props.page));
    const totalPages = computed(() => toValue(props.totalPages));

    const hasNext = computed(() => page.value < totalPages.value);
    const hasPrevious = computed(() => page.value > 1);

    const paginationItems = computed<PaginationItem[]>(() => {
        const result: PaginationItem[] = [];
        const maxItems = 7;

        if (totalPages.value <= maxItems) {
            for (let i = 1; i <= totalPages.value; i++) {
                result.push({ type: "item", page: i });
            }

            return result;
        }

        result.push({ type: "item", page: 1 });

        let start = Math.max(2, page.value - 2);
        let end = Math.min(totalPages.value - 1, page.value + 2);

        if (start <= 2) {
            end = 5;
        }

        if (end >= totalPages.value - 1) {
            start = totalPages.value - 4;
        }

        if (start > 2) {
            result.push({ type: "ellipsis" });
        }

        for (let i = start; i <= end; i++) {
            result.push({ type: "item", page: i });
        }

        if (end < totalPages.value - 1) {
            result.push({ type: "ellipsis" });
        }

        result.push({ type: "item", page: totalPages.value });

        return result;
    });

    function changePage(newPage: number) {
        if (newPage === page.value || props.loading) {
            return;
        }

        emit("loadPage", newPage);
    }
</script>

<template>
    <section>
        <div class="relative w-full h-full">
            <div v-if="loading">
                <slot name="skeleton">
                    <div>
                        <div class="w-full h-full flex items-center justify-center">
                            <slot name="spinner" />
                        </div>
                    </div>
                </slot>
            </div>

            <div v-if="!items || items.length === 0" class="w-full h-full">
                <slot name="empty" />
            </div>

            <div v-if="items" v-bind="$attrs">
                <template v-for="(item, itemIndex) in items" :key="item[props.index]">
                    <slot name="item" v-bind="{ ...item, $item: item, $index: itemIndex }" />
                </template>
            </div>
        </div>

        <Pagination v-if="totalPages > 1" :items-per-page="pageSize" class="mt-6">
            <PaginationContent>
                <PaginationPrevious
                    :disabled="!hasPrevious || props.loading"
                    @click="changePage(page - 1)"
                >
                    <slot name="controls-previous" />
                </PaginationPrevious>

                <template
                    v-for="(item, itemIndex) in paginationItems"
                    :key="`${item.type}-${itemIndex}`"
                >
                    <template v-if="item.type === 'item'">
                        <PaginationItem
                            :value="item.page"
                            :is-active="item.page === page"
                            @click="changePage(item.page)"
                        >
                            {{ item.page }}
                        </PaginationItem>
                    </template>
                    <template v-else>
                        <PaginationEllipsis />
                    </template>
                </template>

                <PaginationNext :disabled="!hasNext || props.loading" @click="changePage(page + 1)">
                    <slot name="controls-next" />
                </PaginationNext>
            </PaginationContent>
        </Pagination>
    </section>
</template>
