<script setup lang="ts">
    import type { z } from "zod";
    import { Upload } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const { schema } = useProjectTabsSharedState();
    const errorToast = useErrorToast();

    function handleSchema() {
        if (!schema.state.value.tableName) {
            toast.error($t("projects.id.sections.schema.validation.table_name_not_empty"));
            return;
        }

        if (!schema.computed.jsonSchema.value || !project.value) {
            return;
        }

        const payload = SchemaUtils.Builder.buildJsonSchema(
            schema.state.value.tableName,
            project.value.id,
            schema.computed.jsonSchema.value,
            [],
        );

        console.warn(payload);
    }

    function handleFile() {
        const parseResult = SchemaUtils.Builder.buildColumnsPayload(
            schema.state.value.columnsConfig,
        );

        if (!parseResult.success || !schema.state.value.uploadedFile?.blob || !project.value) {
            return;
        }

        if (!schema.state.value.tableName) {
            toast.error($t("projects.id.sections.schema.validation.table_name_not_empty"));
            return;
        }

        const dtypes = SchemaUtils.Builder.buildDtypesBySheet(
            schema.state.value.sheetNames,
            parseResult.data,
        );

        const formData = new FormBuilder()
            .append("spreadsheet", schema.state.value.uploadedFile.blob)
            .append("project_id", project.value?.id)
            .append("table_name", schema.state.value.tableName)
            .append("dtypes_str", JSON.stringify(dtypes))
            .build();

        console.warn(Array.from(formData.entries()));
    }

    function handleSubmit(_event: Event) {
        if (!schema.state.value.uploadedFile) {
            errorToast.handle(ResponseCodesRecord.Server.Project.Schema.NoFileProvided);
            return;
        }

        if (schema.state.value.uploadedFile.type === "json") {
            handleSchema();
            return;
        }

        if (["xlsx", "xls", "csv"].includes(schema.state.value.uploadedFile.type)) {
            handleFile();
        }
    }
</script>

<template>
    <AlertDialogContent>
        <AlertDialogHeader>
            <AlertDialogTitle>
                {{ $t("projects.id.sections.schema.upload.title") }}
            </AlertDialogTitle>
            <AlertDialogDescription>
                {{ $t("projects.id.sections.schema.upload.description") }}
            </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
            <AlertDialogAction class="space-x-2" @click="handleSubmit">
                <Upload />
                {{ $t("projects.id.sections.schema.events.upload_file.label") }}
            </AlertDialogAction>
            <AlertDialogCancel> {{ $t("common.actions.cancel") }} </AlertDialogCancel>
        </AlertDialogFooter>
    </AlertDialogContent>
</template>
