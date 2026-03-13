<script setup lang="ts">
    import type { z } from "zod";
    import { Upload } from "lucide-vue-next";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const { schema } = useProjectTabsSharedState();
    const errorToast = useErrorToast();
    const api = useApi();

    function handleSchema() {}
    function handleFile() {}

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
