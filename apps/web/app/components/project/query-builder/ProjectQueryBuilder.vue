<script setup lang="ts">
    import { RotateCcw, Table2, Upload } from "lucide-vue-next";

    const { VIEWS, tables, queryBuilder } = useProject();

    const qb = useProvideQueryBuilder(queryBuilder.state.schema);

    const selectedSchemaName = useRouteQuery(
        "table",
        queryBuilder.state.schema.value?.import_name ?? "",
    );

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

    syncRef(queryBuilder.state.schema, selectedSchemaName, {
        direction: "ltr",
        transform: {
            ltr(left) {
                return left?.import_name;
            },
        },
    });

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
            <CardContent class="h-9">
                <ClientOnly>
                    <Select
                        :model-value="selectedSchemaName"
                        :disabled="!tables.state.value.tableSchemas.length"
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
                            <template
                                v-for="table in tables.state.value.tableSchemas"
                                :key="table.id"
                            >
                                <SelectItem :value="table.import_name">
                                    {{ TableUtils.getTableName(table.import_name) }}
                                </SelectItem>
                            </template>
                        </SelectContent>
                    </Select>

                    <template #fallback>
                        <Skeleton class="h-9 w-64" />
                    </template>
                </ClientOnly>
            </CardContent>
        </Card>

        <ClientOnly>
            <template v-if="queryBuilder.state.schema.value">
                <SchemaQueryBuilder />
            </template>
            <template v-else>
                <Card>
                    <CardContent>
                        <Empty>
                            <EmptyHeader>
                                <EmptyMedia variant="icon">
                                    <Table2 />
                                </EmptyMedia>
                                <EmptyTitle>
                                    {{
                                        $t("projects.id.sections.query_builder.schema_empty.title")
                                    }}
                                </EmptyTitle>
                                <EmptyDescription>
                                    {{
                                        $t(
                                            "projects.id.sections.query_builder.schema_empty.description",
                                        )
                                    }}
                                </EmptyDescription>
                            </EmptyHeader>
                            <EmptyContent>
                                <Button
                                    variant="outline"
                                    class="cursor-pointer"
                                    @click="
                                        events.emit('event:projects:change-tab', {
                                            value: VIEWS.UploadFile,
                                        })
                                    "
                                >
                                    <Upload />
                                    {{ $t("projects.id.sections.upload_schema.tab") }}
                                </Button>
                            </EmptyContent>
                        </Empty>
                    </CardContent>
                </Card>
            </template>

            <template #fallback>
                <Card v-for="index in 4" :key="index">
                    <CardHeader class="space-y-1.5">
                        <Skeleton class="h-4" />
                        <Skeleton class="h-5" />
                    </CardHeader>
                    <CardContent>
                        <Skeleton class="h-64" />
                    </CardContent>
                </Card>
            </template>
        </ClientOnly>
    </div>
</template>
