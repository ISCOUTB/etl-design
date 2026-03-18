<script setup lang="ts">
    import type { z } from "zod";
    import { ArrowLeft } from "lucide-vue-next";

    interface Props {
        schema: MaybeRefOrGetter<z.infer<typeof MongoRawSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const schema = computed(() => toValue(props.schema));
    const tableName = computed(() => {
        if (!schema.value) {
            return;
        }

        return TableUtils.getTableName(schema.value.import_name);
    });

    const events = useAppEvents();
    function handleBack(_event: Event) {
        events.emit("event:projects:table:change-view", { value: "overview" });
    }
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle>{{ tableName }}</CardTitle>
            <CardDescription>
                {{ $t("projects.id.sections.tables.card.selected_schema.description") }}
            </CardDescription>
        </CardHeader>
        <CardContent>
            <div class="space-y-4">
                <CodeBlock class="bg-muted/20" :content="schema" />
                <Button variant="outline" class="cursor-pointer" @click="handleBack">
                    <ArrowLeft />
                    {{ $t("common.actions.go_back") }}
                </Button>
            </div>
        </CardContent>
    </Card>
</template>
