<script setup lang="ts">
    import type { z } from "zod";
    import { Upload } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));
    const events = useAppEvents<AppEvents.Events>();

    const { uploadSchema } = useProject();
    const errorToast = useErrorToast();
    const actions = useProjectTableActions();

    function handleSchema() {
        if (!uploadSchema.state.value.tableName) {
            toast.error($t("projects.id.sections.schema.validation.table_name_not_empty"));
            return;
        }

        if (!uploadSchema.computed.jsonSchema.value || !project.value) {
            return;
        }

        actions
            .uploadSchema(
                project.value,
                uploadSchema.state.value.tableName,
                uploadSchema.computed.jsonSchema.value,
            )
            .then(async () => {
                if (project.value) {
                    await refreshNuxtData(NuxtKeys.Projects.Tables.RawSchemas(project.value.id));
                }

                toast.success($t("projects.id.sections.schema.events.table_created.title"), {
                    description: $t(
                        "projects.id.sections.schema.events.table_created.description",
                        {
                            tab: $t("projects.id.sections.tables.tab"),
                        },
                    ),
                });

                handleCloseModal();
                events.emit("event:schema:table-created", undefined);
            })
            .catch((error) => {
                handleCloseModal();
                errorToast.handleServer(error);
            });
    }

    function handleFile() {
        const parseResult = SchemaUtils.Builder.buildColumnsPayload(
            uploadSchema.state.value.columnsConfig,
        );

        if (
            !parseResult.success ||
            !uploadSchema.state.value.uploadedFile?.blob ||
            !project.value
        ) {
            return;
        }

        if (!uploadSchema.state.value.tableName) {
            toast.error($t("projects.id.sections.schema.validation.table_name_not_empty"));
            return;
        }

        const dtypes = SchemaUtils.Builder.buildDtypesBySheet(
            uploadSchema.state.value.sheetNames,
            parseResult.data,
        );

        actions
            .uploadFile(
                uploadSchema.state.value.uploadedFile.file,
                project.value,
                uploadSchema.state.value.tableName,
                dtypes,
            )
            .then(async () => {
                if (project.value) {
                    await refreshNuxtData(NuxtKeys.Projects.Tables.RawSchemas(project.value.id));
                }

                toast.success($t("projects.id.sections.schema.events.table_created.title"), {
                    description: $t(
                        "projects.id.sections.schema.events.table_created.description",
                        {
                            tab: $t("projects.id.sections.tables.tab"),
                        },
                    ),
                });

                handleCloseModal();
                events.emit("event:schema:table-created", undefined);
            })
            .catch((error) => {
                handleCloseModal();
                errorToast.handleServer(error);
            });
    }

    function handleSubmit(_event: Event) {
        if (!uploadSchema.state.value.uploadedFile) {
            errorToast.handle(ResponseCodesRecord.Server.Project.Schema.NoFileProvided);
            return;
        }

        if (uploadSchema.state.value.uploadedFile.type === "json") {
            handleSchema();
            return;
        }

        if (["xlsx", "xls", "csv"].includes(uploadSchema.state.value.uploadedFile.type)) {
            handleFile();
        }
    }

    const modal = useModal();
    function handleCloseModal() {
        if (modal.state.value.currentModalKey === ModalKeys.Projects.Schema.UploadSchema) {
            modal.dispatch.setOpen(false);
        }
    }
</script>

<template>
    <ResponsiveModal desktop="alert-dialog" mobile="drawer">
        <template #alert-dialog>
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
                    <AlertDialogAction
                        :disabled="actions.state.loading.value"
                        class="space-x-2"
                        @click="handleSubmit"
                    >
                        <Upload />
                        {{ $t("projects.id.sections.schema.events.upload_file.label") }}
                    </AlertDialogAction>
                    <AlertDialogCancel> {{ $t("common.actions.cancel") }} </AlertDialogCancel>
                </AlertDialogFooter>
            </AlertDialogContent>
        </template>
        <template #drawer>
            <DrawerContent>
                <DrawerHeader>
                    <DrawerTitle>
                        {{ $t("projects.id.sections.schema.upload.title") }}
                    </DrawerTitle>
                    <DrawerDescription>
                        {{ $t("projects.id.sections.schema.upload.description") }}
                    </DrawerDescription>
                </DrawerHeader>

                <DrawerFooter>
                    <div class="flex justify-end space-x-4">
                        <Button
                            :disabled="actions.state.loading.value"
                            class="space-x-2"
                            @click="handleSubmit"
                        >
                            <Upload />
                            {{ $t("projects.id.sections.schema.events.upload_file.label") }}
                        </Button>
                        <Button variant="outline" @click="handleCloseModal">
                            {{ $t("common.actions.cancel") }}
                        </Button>
                    </div>
                </DrawerFooter>
            </DrawerContent>
        </template>
    </ResponsiveModal>
</template>
