<script setup lang="ts">
    import { ArrowLeft, Plus, RotateCcw, Save, Trash2 } from "lucide-vue-next";

    interface ColumnDefinition {
        name: string;
        type: Dtype;
        unique: boolean;
        optional: boolean;
        primary_key: boolean;
    }

    definePageMeta({
        title: "projects.id.tables.edit.header.title",
        layout: "sidebar",
        middleware: ["table-validation", "internal-callback-url"],
        i18n: {
            paths: {
                en: "/projects/[id]/tables/[tableName]",
            },
        },
    });

    useSeoMeta({
        title: $t("projects.id.tables.edit.header.title"),
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

    const initialValues = {
        tableName: tableName.value,
        columns: Object.entries(sharedState.value.active_schema.properties).map<ColumnDefinition>(
            ([name, def]) => ({
                name,
                type: def.type || "string",
                optional: !!def.optional || false,
                unique: !!def.unique || false,
                primary_key: !!def.primary_key || false,
            }),
        ),
    };

    const { EditTableSchema } = useEditTableSchema();
    const { meta, handleSubmit, resetField, setFieldValue, resetForm } = useForm({
        validationSchema: toTypedSchema(EditTableSchema.value),
        initialValues,
    });
    const { fields, push, remove } = useFieldArray<ColumnDefinition>("columns");
    const columnsDirty = computed(
        () =>
            JSON.stringify(fields.value.map((field) => field.value)) ===
            JSON.stringify(initialValues.columns),
    );

    const router = useRouter();
    const errorToast = useErrorToast();
    const api = useApi();
    const [loading] = useToggle(false);
    const onSubmit = handleSubmit((values) => {
        loading.value = true;

        api(`/schemas/${projectId.value}`, {
            method: "POST",
            query: {
                table_name: values.tableName,
            },
            body: {
                $schema: sharedState.value.active_schema.$schema,
                type: sharedState.value.active_schema.type,
                required: values.columns
                    .filter((column) => !column.optional)
                    .map((column) => column.name),
                properties: Object.fromEntries(
                    values.columns.map(({ name, ...options }) => [name, options]),
                ),
            },
        })
            .then(async () => {
                await refreshNuxtData(NuxtKeys.Projects.Tables.RawSchemas(projectId.value));
                clearNuxtData(KEY);

                router.push(callbackUrl.value);
            })
            .catch((error) => errorToast.handleServer(error))
            .finally(() => (loading.value = false));
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
                        <h1 class="text-2xl font-semibold text-foreground">
                            {{ $t("projects.id.tables.edit.header.title") }}
                        </h1>
                        <p class="mt-1 text-sm text-muted-foreground">
                            {{ $t("projects.id.tables.edit.header.description") }}
                        </p>
                    </div>
                    <div class="flex gap-2">
                        <Button
                            type="button"
                            variant="outline"
                            :disabled="!meta.dirty"
                            @click="resetForm"
                        >
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
                    <CardTitle class="text-base">
                        {{ $t("projects.id.tables.edit.project_information") }}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <VeeField v-slot="{ field, errors, meta: fieldMeta }" name="tableName">
                        <Field :data-invalid="!!errors.length">
                            <FieldLabel for="tableName">
                                {{ $t("projects.id.tables.edit.fields.table_name") }}
                            </FieldLabel>
                            <InputGroup>
                                <InputGroupInput
                                    id="tableName"
                                    disabled
                                    v-bind="field"
                                    :model-value="field.value"
                                    :aria-invalid="!!errors.length"
                                    class="font-mono"
                                />
                                <InputGroupAddon v-if="fieldMeta.dirty" align="inline-end">
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
                            <FieldDescription>
                                {{
                                    $t("projects.id.tables.edit.fields.table_id", {
                                        id: sharedState.id,
                                    })
                                }}
                            </FieldDescription>
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>
                </CardContent>
            </Card>

            <Card>
                <VeeFieldArray name="columns">
                    <CardHeader>
                        <CardTitle>
                            <div class="flex items-center justify-between">
                                <CardTitle class="text-base">
                                    {{ $t("projects.id.tables.edit.columns.title") }}
                                    <Badge variant="secondary" class="ml-2 font-normal">
                                        {{ fields.length }}
                                    </Badge>
                                </CardTitle>
                                <div class="flex gap-2">
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        :disabled="columnsDirty"
                                        @click="setFieldValue('columns', initialValues.columns)"
                                    >
                                        <RotateCcw class="size-4" />
                                        {{ $t("projects.id.tables.edit.buttons.reset") }}
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
                                                    optional: false,
                                                    primary_key: false,
                                                    unique: false,
                                                })
                                        "
                                    >
                                        <Plus class="size-4" />
                                        {{ $t("projects.id.tables.edit.columns.add") }}
                                    </Button>
                                </div>
                            </div>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div class="flex flex-col gap-3">
                            <template v-if="fields.length">
                                <div
                                    class="grid grid-cols-4 lg:grid-cols-12 gap-3 px-3 text-xs font-medium text-muted-foreground"
                                >
                                    <div class="col-span-1 lg:col-span-4">
                                        {{ $t("projects.id.tables.edit.columns.name") }}
                                    </div>
                                    <div class="col-span-2 lg:col-span-4">
                                        {{ $t("projects.id.tables.edit.columns.type") }}
                                    </div>
                                    <div class="hidden lg:block col-span-1 text-center">
                                        Primary
                                    </div>
                                    <div class="hidden lg:block col-span-1 text-center">Unique</div>
                                    <div class="hidden lg:block col-span-1 text-center">
                                        Optional
                                    </div>
                                    <div class="col-span-1" />
                                </div>

                                <div
                                    v-for="(column, index) in fields"
                                    :key="column.key"
                                    class="grid grid-cols-4 lg:grid-cols-12 items-start gap-3 bg-card"
                                >
                                    <div class="col-span-1 lg:col-span-4">
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
                                    <div class="col-span-2 lg:col-span-4">
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
                                    <div
                                        class="col-span-1 hidden lg:flex items-center justify-center pt-2"
                                    >
                                        <VeeField
                                            v-slot="{ handleChange, value }"
                                            :name="`columns[${index}].primary_key`"
                                            type="checkbox"
                                            :value="true"
                                            :unchecked-value="false"
                                        >
                                            <Checkbox
                                                :disabled="
                                                    fields.some(
                                                        (f, i) =>
                                                            i !== index && f.value.primary_key,
                                                    )
                                                "
                                                :model-value="value === true || value === 'true'"
                                                @update:model-value="handleChange"
                                            />
                                        </VeeField>
                                    </div>
                                    <div
                                        class="col-span-1 hidden lg:flex items-center justify-center pt-2"
                                    >
                                        <VeeField
                                            v-slot="{ handleChange, value }"
                                            :name="`columns[${index}].unique`"
                                            type="checkbox"
                                            :value="true"
                                            :unchecked-value="false"
                                        >
                                            <Checkbox
                                                :model-value="value === true || value === 'true'"
                                                @update:model-value="handleChange"
                                            />
                                        </VeeField>
                                    </div>
                                    <div
                                        class="col-span-1 hidden lg:flex items-center justify-center pt-2"
                                    >
                                        <VeeField
                                            v-slot="{ handleChange, value }"
                                            :name="`columns[${index}].optional`"
                                            type="checkbox"
                                            :value="true"
                                            :unchecked-value="false"
                                        >
                                            <Checkbox
                                                :model-value="value === true || value === 'true'"
                                                @update:model-value="handleChange"
                                            />
                                        </VeeField>
                                    </div>
                                    <div class="col-span-1 flex justify-end pt-2">
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
