<script setup lang="ts" generic="TData">
    import { provideDataTableItemsContext, useDataTableContext } from "./utils";

    interface Props {
        hasNext?: MaybeRefOrGetter<boolean>;
        loading?: MaybeRefOrGetter<boolean>;
    }

    interface Emits {
        loadMode: [];
    }

    const props = withDefaults(defineProps<Props>(), {
        hasNext: false,
        loading: false,
    });
    const emit = defineEmits<Emits>();

    const context = useDataTableContext<TData>();
    const sentinel = useTemplateRef("sentinel");

    const hasNext = computed(() => toValue(props.hasNext));
    const loading = computed(() => toValue(props.loading));

    provideDataTableItemsContext(context.sortedData);

    function loadMore() {
        if (!hasNext.value || loading.value) {
            return;
        }

        emit("loadMode");
    }

    useIntersectionObserver(
        sentinel,
        ([entry]) => {
            if (entry?.isIntersecting) {
                loadMore();
            }
        },
        { root: context.container.value, rootMargin: "120px", threshold: 0 },
    );
</script>

<template>
    <slot v-bind="{ items: context.sortedData.value, loadMore, container: context.container }" />
    <tr ref="sentinel" aria-hidden="true" />
</template>
