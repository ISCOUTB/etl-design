<script setup lang="ts">
    import { ArrowLeft, Plus, RotateCcw, Save, Trash2 } from "lucide-vue-next";

    definePageMeta({
        title: "projects.id.tables.edit.title",
        layout: "sidebar",
        middleware: ["table-validation", "internal-callback-url"],
        i18n: {
            paths: {
                en: "/projects/[id]/tables/[tableName]",
            },
        },
    });

    useSeoMeta({
        title: $t("projects.id.tables.edit.title"),
        ogType: "website",
    });

    const projectId = useRouteParams("id", NuxtKeys.Params.NoDefaultValue, {
        transform: (value) => value.toString(),
    });
    const tableName = useRouteParams("tableName", NuxtKeys.Params.NoDefaultValue, {
        transform: (value) => value.toString(),
    });
    const setI18nParams = useSetI18nParams();
    setI18nParams({ en: { id: projectId.value, tableName: tableName.value } });

    const { $localePath } = useNuxtApp();
    const callbackUrl = useRouteQuery(
        "callbackUrl",
        $localePath({ name: "projects-id", params: { id: projectId.value } }),
    );
    const KEY = NuxtKeys.Projects.Tables.SharedState(projectId.value, tableName.value);
    const sharedState = useState<MongoRaw>(KEY);

    const { EditTableSchema } = useEditTableSchema();
    const { meta, handleSubmit, resetField } = useForm({
        validationSchema: toTypedSchema(EditTableSchema.value),
        initialValues: {
            tableName: tableName.value,
            columns: Object.entries(sharedState.value.active_schema.properties).map(
                ([name, def]) => ({ name, ...def }),
            ),
        },
    });

    const onSubmit = handleSubmit((values) => {
        console.warn(values);
    });
</script>

<template>
    <div class="mx-auto w-full max-w-5xl">
        <form class="space-y-4" @submit="onSubmit">
            <div class="flex flex-col gap-4">
                <Button type="button" variant="ghost" size="sm" class="w-fit -ml-2" as-child>
                    <NuxtLink :to="callbackUrl">
                        <ArrowLeft />
                        <span>
                            {{ $t("common.actions.go_back") }}
                        </span>
                    </NuxtLink>
                </Button>

                <div class="flex items-start justify-between gap-4">
                    <div>
                        <h1 class="text-2xl font-semibold text-foreground">Edit Table</h1>
                        <p class="mt-1 text-sm text-muted-foreground">
                            Modify the schema definition for this table
                        </p>
                    </div>
                    <div class="flex gap-2">
                        <Button type="button" variant="outline" :disabled="!meta.dirty">
                            {{ $t("common.actions.reset") }}
                        </Button>
                        <Button type="submit" :disabled="!meta.dirty || !meta.valid">
                            <Save class="size-4" />
                            {{ $t("common.actions.save_changes") }}
                        </Button>
                    </div>
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle class="text-base"> Project Information </CardTitle>
                </CardHeader>
                <CardContent>
                    <VeeField v-slot="{ field, errors }" name="tableName">
                        <Field :data-invalid="!!errors.length">
                            <FieldLabel for="tableName"> Table Name </FieldLabel>
                            <InputGroup>
                                <InputGroupInput
                                    id="tableName"
                                    v-bind="field"
                                    :model-value="field.value"
                                    :aria-invalid="!!errors.length"
                                    class="font-mono"
                                />
                                <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                    <InputGroupButton
                                        variant="ghost"
                                        size="icon-xs"
                                        type="button"
                                        @click="resetField('tableName')"
                                    >
                                        <RotateCcw class="size-4" />
                                    </InputGroupButton>
                                </InputGroupAddon>
                            </InputGroup>
                            <FieldDescription> ID: {{ sharedState.id }} </FieldDescription>
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>
                </CardContent>
            </Card>

            <Card>
                <VeeFieldArray v-slot="{ fields, push, remove }" name="columns">
                    <CardHeader>
                        <CardTitle>
                            <div class="flex items-center justify-between">
                                <CardTitle class="text-base">
                                    Columns
                                    <Badge variant="secondary" class="ml-2 font-normal">
                                        {{ fields.length }}
                                    </Badge>
                                </CardTitle>
                                <div class="flex gap-2">
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        @click="resetField('columns')"
                                    >
                                        <RotateCcw class="size-4" />
                                        {{ $t("common.actions.reset") }}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        @click="
                                            () =>
                                                push({
                                                    name: $t(
                                                        'projects.id.sections.tables.default_table_name',
                                                    ),
                                                    type: 'string',
                                                })
                                        "
                                    >
                                        <Plus class="size-4" />
                                        Add Column
                                    </Button>
                                </div>
                            </div>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div class="flex flex-col gap-3">
                            <template v-if="fields.length">
                                <div
                                    class="grid grid-cols-12 gap-3 px-3 text-xs font-medium text-muted-foreground"
                                >
                                    <div class="col-span-5">Column Name</div>
                                    <div class="col-span-6">Column Type</div>
                                    <div class="col-span-1" />
                                </div>

                                <div
                                    v-for="(column, index) in fields"
                                    :key="column.key"
                                    class="grid grid-cols-12 items-start gap-3 bg-card"
                                >
                                    <div class="col-span-5">
                                        <VeeField
                                            v-slot="{ field, errors }"
                                            :name="`columns[${index}].name`"
                                        >
                                            <Field :data-invalid="!!errors.length">
                                                <Input
                                                    v-bind="field"
                                                    :model-value="field.value"
                                                    class="font-mono text-sm"
                                                    placeholder="column_name"
                                                    :aria-invalid="!!errors.length"
                                                />
                                                <FieldError v-if="errors.length" :errors="errors" />
                                            </Field>
                                        </VeeField>
                                    </div>
                                    <div class="col-span-6">
                                        <VeeField
                                            v-slot="{ field, errors }"
                                            :name="`columns[${index}].type`"
                                        >
                                            <Field :data-invalid="!!errors.length">
                                                <SchemaDataTypeSelect
                                                    v-bind="field"
                                                    :model-value="field.value"
                                                />
                                                <FieldError v-if="errors.length" :errors="errors" />
                                            </Field>
                                        </VeeField>
                                    </div>
                                    <div class="col-span-1 flex justify-end">
                                        <Button
                                            variant="destructive"
                                            size="icon"
                                            @click="remove(index)"
                                        >
                                            <Trash2 class="size-4" />
                                            <span class="sr-only">
                                                {{ $t("common.actions.remove") }}
                                            </span>
                                        </Button>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </CardContent>
                </VeeFieldArray>
            </Card>
        </form>
    </div>
</template>
