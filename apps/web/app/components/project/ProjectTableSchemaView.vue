<script setup lang="ts">
    import type { z } from "zod";

    interface Props {
        schema: z.infer<typeof MongoRawSchema>;
    }

    const props = defineProps<Props>();
    const tableName = computed(() => TableUtils.getTableName(props.schema.import_name));
</script>

<template>
    <DialogContent>
        <DialogHeader>
            <DialogTitle>{{ tableName }}</DialogTitle>
            <DialogDescription>
                {{ $t("projects.id.sections.tables.card.modal.description") }}
            </DialogDescription>
        </DialogHeader>
        <CodeBlock :content="schema" />
    </DialogContent>
</template>
