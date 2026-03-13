<script setup lang="ts">
    import { Upload } from "lucide-vue-next";

    const state = useProjectTabsSharedState();
    const errorToast = useErrorToast();
    const api = useApi();

    function handleSchema() {}
    function handleFile() {}

    function handleSubmit(_event: Event) {
        if (!state.uploadedFile.value) {
            errorToast.handle(ResponseCodesRecord.Server.Project.Schema.NoFileProvided);
            return;
        }

        if (state.uploadedFile.value.type === "json") {
            handleSchema();
            return;
        }

        if (["xlsx", "xls", "csv"].includes(state.uploadedFile.value.type)) {
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
