<!-- TODO: Add pagination Mode: "server" | "client" -->

<script setup lang="ts" generic="TData">
    import { ChevronsLeft, ChevronsRight } from "lucide-vue-next";
    import {
        provideDataTableItemsContext,
        useDataTableContext,
    } from "@/components/common/data-table/utils";

    interface Props {
        currentPage: MaybeRefOrGetter<number>;
        hasNext?: MaybeRefOrGetter<boolean>;
        hasPrevious?: MaybeRefOrGetter<boolean>;
        loading?: MaybeRefOrGetter<boolean>;
        showControls?: boolean;
    }

    interface Emits {
        next: [];
        previous: [];
    }

    const props = withDefaults(defineProps<Props>(), {
        hasNext: false,
        hasPrevious: false,
        loading: false,
        showControls: true,
    });

    const emit = defineEmits<Emits>();

    const context = useDataTableContext<TData>();
    const currentPage = computed(() => toValue(props.currentPage));
    const loading = computed(() => toValue(props.loading));
    const hasNext = computed(() => toValue(props.hasNext));
    const hasPrevious = computed(() => toValue(props.hasPrevious));

    function nextPage() {
        if (!hasNext.value || loading.value) {
            return;
        }

        emit("next");
    }

    function previousPage() {
        if (!hasPrevious.value || loading.value) {
            return;
        }

        emit("previous");
    }

    provideDataTableItemsContext(context.sortedData);
</script>

<template>
    <slot v-bind="{ items: context.sortedData.value }" />

    <div v-if="showControls" class="mt-4">
        <slot
            name="pagination"
            v-bind="{ currentPage, hasNext, hasPrevious, nextPage, previousPage, loading }"
        >
            <div class="flex items-center justify-end space-x-2">
                <Button
                    type="button"
                    variant="ghost"
                    :disabled="!hasPrevious || loading"
                    @click="previousPage"
                >
                    <ChevronsLeft class="size-4" />
                </Button>
                <Button
                    type="button"
                    variant="ghost"
                    :disabled="!hasNext || loading"
                    @click="nextPage"
                >
                    <ChevronsRight class="size-4" />
                </Button>
            </div>
        </slot>
    </div>
</template>
