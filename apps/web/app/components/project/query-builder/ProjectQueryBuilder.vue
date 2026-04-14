<script setup lang="ts">
    import { RotateCcw } from "lucide-vue-next";

    const { tables, queryBuilder } = useProject();

    const qb = useProvideQueryBuilder(queryBuilder.state.schema);
    const selectedSchemaName = computed(() => queryBuilder.state.schema.value?.import_name ?? "");

    watchEffect(() => {
        const list = tables.state.value.tableSchemas;
        if (!list.length) {
            queryBuilder.state.schema.value = undefined;
            return;
        }

        const current = queryBuilder.state.schema.value;
        const stillExists = current
            ? list.some((s) => s.import_name === current.import_name)
            : false;

        if (!stillExists) {
            queryBuilder.state.schema.value = list[0];
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
            queryBuilder.state.schema.value = found;
        }
    }

    const events = useAppEvents();
    onMounted(() => {
        events.on("event:projects:query-builder:reset", () => qb.dispatch.reset());
    });
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
                        <div class="space-x-2">
                            <Button
                                variant="outline"
                                class="cursor-pointer"
                                @click="
                                    events.emit('event:projects:query-builder:reset', undefined)
                                "
                            >
                                <RotateCcw />
                                {{ $t("common.actions.reset") }}
                            </Button>
                            <ProjectQueryBuilderGenerate />
                        </div>
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
        <template v-if="queryBuilder.state.schema.value">
            <SchemaQueryBuilder />
        </template>
        <template v-else>
            <p class="text-sm text-muted-foreground">
                {{ $t("projects.id.sections.query_builder.schema.empty") }}
            </p>
        </template>
    </div>
</template>
