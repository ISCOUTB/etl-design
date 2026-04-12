<script setup lang="ts">
    import { RotateCcw } from "lucide-vue-next";

    const { tables } = useProject();
    const schema = useState<MongoRaw | undefined>("project:query-builder:schema", () => undefined);

    const selectedSchemaName = computed(() => schema.value?.import_name ?? "");

    watchEffect(() => {
        const list = tables.state.value.tableSchemas;
        if (!list.length) {
            schema.value = undefined;
            return;
        }

        const current = schema.value;
        const stillExists = current
            ? list.some((s) => s.import_name === current.import_name)
            : false;

        if (!stillExists) {
            schema.value = list[0];
        }
    });

    function onSchemaChange(payload?: string) {
        if (!payload) {
            return;
        }

        const found = tables.state.value.tableSchemas.find(
            (_schema) => _schema.import_name === payload,
        );

        if (found) {
            schema.value = found;
        }
    }

    const events = useAppEvents();
</script>

<template>
    <div class="space-y-4">
        <Card>
            <CardHeader>
                <Item class="p-0">
                    <ItemContent>
                        <ItemTitle as-child>
                            <CardTitle>
                                {{ $t("projects.id.sections.query_builder.title") }}
                            </CardTitle>
                        </ItemTitle>
                        <ItemDescription as-child>
                            {{ $t("projects.id.sections.query_builder.description") }}
                        </ItemDescription>
                    </ItemContent>
                    <ItemActions>
                        <Button
                            variant="outline"
                            @click="events.emit('event:projects:query-builder:reset', undefined)"
                        >
                            <RotateCcw />
                            {{ $t("common.actions.reset") }}
                        </Button>
                    </ItemActions>
                </Item>
            </CardHeader>
            <CardContent class="space-y-4">
                <Select
                    :model-value="selectedSchemaName"
                    @update:model-value="onSchemaChange($event?.toString())"
                >
                    <SelectTrigger class="w-64">
                        <SelectValue
                            :placeholder="
                                $t('projects.id.sections.query_builder.schema.placeholder')
                            "
                        />
                    </SelectTrigger>
                    <SelectContent :body-lock="false">
                        <template v-for="table in tables.state.value.tableSchemas" :key="table.id">
                            <SelectItem :value="table.import_name">
                                {{ TableUtils.getTableName(table.import_name) }}
                            </SelectItem>
                        </template>
                    </SelectContent>
                </Select>
            </CardContent>
        </Card>
        <template v-if="schema">
            <SchemaQueryBuilder :schema="schema" />
        </template>
        <template v-else>
            <p class="text-sm text-muted-foreground">
                {{ $t("projects.id.sections.query_builder.schema.empty") }}
            </p>
        </template>
    </div>
</template>
