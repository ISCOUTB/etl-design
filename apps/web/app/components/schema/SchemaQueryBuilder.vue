<script setup lang="ts">
    interface Props {
        schema: MaybeRefOrGetter<MongoRaw>;
    }

    const props = defineProps<Props>();
    const schema = computed(() => toValue(props.schema));

    const qb = useProvideQueryBuilder(schema);

    const events = useAppEvents();
    onMounted(() => {
        events.on("event:projects:query-builder:reset", () => qb.dispatch.reset());
    });
</script>

<template>
    <div class="space-y-4">
        <SchemaQueryBuilderCardSelectColumn />
        <SchemaQueryBuilderCardConditions />
        <SchemaQueryBuilderCardOptions />
        <SchemaQueryBuilderOutput :schema="schema" />
    </div>
</template>
