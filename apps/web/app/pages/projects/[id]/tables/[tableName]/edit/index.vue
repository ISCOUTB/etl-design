<script setup lang="ts">
    import { ArrowLeft, Save, RotateCcw } from "lucide-vue-next";

    interface ColumnDefinition {
        name: string;
        type: Dtype;
        extra: Record<string, unknown>;
    }

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
        <form @submit="onSubmit">
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
                        <Button type="submit">
                            <Save class="size-4" :disabled="!meta.dirty || !meta.valid" />
                            {{ $t("common.actions.save_changes") }}
                        </Button>
                    </div>
                </div>
            </div>

            <Card class="mt-4">
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
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>
                </CardContent>
            </Card>
        </form>
    </div>
</template>
