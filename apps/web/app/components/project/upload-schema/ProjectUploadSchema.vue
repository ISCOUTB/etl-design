<script setup lang="ts">
    import { filesize } from "filesize";
    import {
        Download,
        FileIcon,
        FileJson,
        FileSpreadsheet,
        TriangleAlert,
        X,
    } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    const {
        state: { project },
        uploadSchema,
    } = useProject();

    const events = useAppEvents();

    const fileURL = useObjectUrl(() => uploadSchema.state.value.uploadedFile?.blob);
    const shouldShowExample = computed(
        () =>
            !uploadSchema.state.value.uploadedFile ||
            (uploadSchema.state.value.uploadedFile &&
                uploadSchema.state.value.uploadedFile.type === "json"),
    );

    const actions = useProjectUploadFileActions();

    const config = useAppConfig();
    const selectedFile = computed({
        get() {
            return uploadSchema.state.value.uploadedFile;
        },
        set(value) {
            uploadSchema.dispatch.setUploadedFile(value);
        },
    });
    function handleFile(file: File) {
        actions.processFile(file, {
            supportedFormats: config.files.uploadSchema.supportedFormats,
            mimeTypes: config.files.uploadSchema.supportedMimeTypes,
            onError() {
                toast.error($t("errors.project.file_not_supported.title"), {
                    description: $t("errors.project.file_not_supported.description"),
                });
            },
            onSuccess(file, extension, mime) {
                selectedFile.value = {
                    name: file.name,
                    nameWithoutExt: file.name.replace(/\.[^/.]+$/, ""),
                    size: filesize(file.size),
                    type: extension,
                    file,
                    blob: new Blob([file], { type: mime }),
                };
            },
        });
    }

    function handleInputChange(event: Event) {
        if (!(event.target instanceof HTMLInputElement)) {
            return;
        }

        const element = event.target;
        const file = element.files?.[0];
        if (!file) {
            return;
        }

        handleFile(file);
    }

    const dataTypeModels = computed(() =>
        Object.fromEntries(
            uploadSchema.computed.columns.value.map((column) => [
                String(column.key),
                uploadSchema.dispatch.getColumnDataTypeModel(String(column.key)),
            ]),
        ),
    );

    const animations = useProjectSchemaAnimations();
    const modal = useModal();
    const canSubmit = computed<boolean>(() => {
        const uploaded = selectedFile.value;
        const hasFile = !!uploaded && uploaded.blob.size > 0;
        const hasValidTableName = (uploadSchema.state.value.tableName?.trim().length ?? 0) > 0;
        const hasErrors = uploadSchema.errors.value.length > 0;

        return hasFile && hasValidTableName && !hasErrors;
    });

    const errorToast = useErrorToast();
    const tableActions = useProjectTableActions();

    function handleCloseModal() {
        if (modal.state.value.currentModalKey === ModalKeys.Projects.Schema.UploadSchema) {
            modal.dispatch.setOpen(false);
        }
    }

    const [loading] = useToggle(false);

    function _uploadSchema() {
        if (!uploadSchema.state.value.tableName) {
            toast.error($t("projects.id.sections.upload_schema.validation.table_name_not_empty"));
            return;
        }

        if (!uploadSchema.computed.jsonSchema.value || !project.value) {
            return;
        }

        tableActions
            .uploadSchema(
                project.value,
                uploadSchema.state.value.tableName,
                uploadSchema.computed.jsonSchema.value,
            )
            .then(async () => {
                if (project.value) {
                    await refreshNuxtData(NuxtKeys.Projects.Tables.RawSchemas(project.value.id));
                }

                toast.success($t("projects.id.sections.upload_schema.events.table_created.title"), {
                    description: $t(
                        "projects.id.sections.upload_schema.events.table_created.description",
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
            })
            .finally(() => (loading.value = false));
    }

    function _uploadFile() {
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
            toast.error($t("projects.id.sections.upload_schema.validation.table_name_not_empty"));
            return;
        }

        const dtypes = SchemaUtils.Builder.buildDtypesBySheet(
            uploadSchema.state.value.sheetNames,
            parseResult.data,
        );

        tableActions
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

                toast.success($t("projects.id.sections.upload_schema.events.table_created.title"), {
                    description: $t(
                        "projects.id.sections.upload_schema.events.table_created.description",
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
            })
            .finally(() => (loading.value = false));
    }

    function handleUpload(_event: Event) {
        modal.dispatch.loadComponent({
            loader: () => import("~/components/project/upload-schema/ProjectUploadSchemaModal.vue"),
            key: ModalKeys.Projects.Schema.UploadSchema,
            kind: "alert-dialog",
            props: {
                project,
                onSubmit() {
                    if (!uploadSchema.state.value.uploadedFile) {
                        errorToast.handle(ResponseCodesRecord.Server.Project.Schema.NoFileProvided);
                        return;
                    }

                    loading.value = true;

                    if (uploadSchema.state.value.uploadedFile.type === "json") {
                        _uploadSchema();
                        return;
                    }

                    if (
                        ["xlsx", "xls", "csv"].includes(uploadSchema.state.value.uploadedFile.type)
                    ) {
                        _uploadFile();
                    }
                },
            },
        });
    }

    onMounted(() => {
        events.on("event:schema:table-created", () => {
            uploadSchema.dispatch.setUploadedFile(undefined);
        });
    });
</script>

<template>
    <div class="space-y-4">
        <section class="space-y-4">
            <div class="space-y-1">
                <h3 class="text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.upload_schema.header.title") }}
                </h3>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.upload_schema.header.description") }}
                </p>
            </div>

            <div class="space-y-4">
                <div class="grid gap-4 sm:grid-cols-2">
                    <Item variant="outline">
                        <ItemMedia>
                            <div class="bg-emerald-500/10 p-2 rounded-md">
                                <FileSpreadsheet class="size-5 text-emerald-500" />
                            </div>
                        </ItemMedia>
                        <ItemContent>
                            <ItemTitle class="font-medium text-foreground"> Excel / CSV </ItemTitle>
                            <ItemDescription>
                                {{
                                    $t("projects.id.sections.upload_schema.cards.supported_formats")
                                }}
                            </ItemDescription>
                        </ItemContent>
                    </Item>
                    <Item variant="outline">
                        <ItemMedia>
                            <div class="bg-amber-500/10 p-2 rounded-md">
                                <FileJson class="size-5 text-amber-500" />
                            </div>
                        </ItemMedia>
                        <ItemContent>
                            <ItemTitle>
                                {{ $t("projects.id.sections.upload_schema.cards.json_schema") }}
                            </ItemTitle>
                            <ItemDescription>
                                {{ $t("projects.id.sections.upload_schema.cards.upload_json") }}
                            </ItemDescription>
                        </ItemContent>
                    </Item>
                </div>

                <DropzoneArea
                    :state="selectedFile"
                    :supported-formats="
                        config.files.uploadSchema.supportedFormats
                            .map((format) => `.${format}`)
                            .join(',')
                    "
                    :dropzone-options="{ multiple: false }"
                    @dropped="
                        (files) => {
                            const file = files?.[0];
                            if (file) {
                                handleFile(file);
                            }
                        }
                    "
                    @change="handleInputChange"
                >
                    <template #file-selected="{ state }">
                        <div>
                            <Item variant="outline">
                                <ItemMedia>
                                    <div class="bg-emerald-500/10 p-2 rounded-md">
                                        <FileIcon class="size-5 text-emerald-500" />
                                    </div>
                                </ItemMedia>
                                <ItemContent>
                                    <ItemTitle class="truncate font-medium text-foreground">
                                        {{ state.name }}
                                    </ItemTitle>
                                    <ItemDescription>
                                        {{ state.size }}
                                    </ItemDescription>
                                </ItemContent>
                                <ItemActions>
                                    <Button v-if="fileURL" as-child variant="ghost">
                                        <NuxtLink :to="fileURL" :download="state.name">
                                            <Download class="size-4" />
                                        </NuxtLink>
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        class="cursor-pointer"
                                        @click="uploadSchema.dispatch.setUploadedFile(undefined)"
                                    >
                                        <X class="size-4" />
                                    </Button>
                                </ItemActions>
                            </Item>
                        </div>
                    </template>
                </DropzoneArea>
            </div>
        </section>

        <Transition
            appear
            mode="out-in"
            @enter="animations.onSchemaEnter"
            @leave="animations.onSchemaLeave"
        >
            <div v-if="shouldShowExample">
                <ProjectUploadSchemaForm
                    v-if="selectedFile"
                    :can-submit="canSubmit"
                    :loading="loading"
                    class="space-y-6"
                    @submit="handleUpload"
                />

                <ProjectUploadSchemaExample />
            </div>
            <div v-else class="space-y-6">
                <div v-if="uploadSchema.errors.value.length > 0">
                    <Alert variant="destructive" class="bg-muted/10">
                        <TriangleAlert />
                        <AlertTitle>Warnings</AlertTitle>
                        <AlertDescription>
                            <ul class="list-inside list-disc space-y-1">
                                <li v-for="error in uploadSchema.errors.value" :key="error.key">
                                    <template v-if="$te(error.message)">
                                        {{ $t(error.message) }}
                                    </template>
                                    <template v-else>
                                        {{ error.message }}
                                    </template>
                                </li>
                            </ul>
                        </AlertDescription>
                    </Alert>
                </div>

                <div class="space-y-1">
                    <h3 className="text-sm font-medium text-foreground">
                        {{ $t("projects.id.sections.upload_schema.datatype_table.title") }}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        {{ $t("projects.id.sections.upload_schema.datatype_table.description") }}
                    </p>
                </div>

                <div class="rounded-lg border overflow-hidden">
                    <Table>
                        <TableHeader>
                            <TableRow class="hover:bg-amber-300/30">
                                <TableHead class="p-4">
                                    {{
                                        $t(
                                            "projects.id.sections.upload_schema.datatype_table.header.column",
                                        )
                                    }}
                                </TableHead>
                                <TableHead class="p-4">
                                    {{
                                        $t(
                                            "projects.id.sections.upload_schema.datatype_table.header.sample_value",
                                        )
                                    }}
                                </TableHead>
                                <TableHead class="p-4">
                                    {{
                                        $t(
                                            "projects.id.sections.upload_schema.datatype_table.header.data_type",
                                        )
                                    }}
                                </TableHead>
                                <TableHead> Primary </TableHead>
                                <TableHead> Unique </TableHead>
                                <TableHead> Optional </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            <TableRow
                                v-for="column in uploadSchema.computed.columns.value"
                                :key="column.key"
                                class="hover:bg-amber-300/10"
                            >
                                <TableCell class="font-mono text-sm px-4">
                                    {{ column.label }}
                                </TableCell>
                                <TableCell class="px-4 py-2 text-muted-foreground">
                                    <span
                                        class="truncate rounded bg-muted px-2 py-0.5 font-mono text-xs"
                                    >
                                        {{
                                            uploadSchema.computed.sampleValueByColumn.value[
                                                column.key
                                            ]
                                        }}
                                    </span>
                                </TableCell>
                                <TableCell class="px-4 py-2">
                                    <SchemaDataTypeSelect
                                        v-model:model-value="
                                            dataTypeModels[String(column.key)]!.value
                                        "
                                        default-value="text"
                                    />
                                </TableCell>
                                <TableCell class="px-4 py-2">
                                    <Checkbox
                                        :disabled="
                                            Object.entries(
                                                uploadSchema.state.value.columnsConfig,
                                            ).some(([k, v]) => v.primary_key && k !== column.key)
                                        "
                                        :model-value="
                                            uploadSchema.state.value.columnsConfig?.[column.key]
                                                ?.primary_key ?? false
                                        "
                                        @update:model-value="
                                            (value) =>
                                                uploadSchema.dispatch.setColumnPrimaryKey(
                                                    column.key,
                                                    !!value,
                                                )
                                        "
                                    />
                                </TableCell>
                                <TableCell class="px-4 py-2">
                                    <Checkbox
                                        :model-value="
                                            uploadSchema.state.value.columnsConfig?.[column.key]
                                                ?.unique ?? false
                                        "
                                        @update:model-value="
                                            (value) =>
                                                uploadSchema.dispatch.setColumnUnique(
                                                    column.key,
                                                    !!value,
                                                )
                                        "
                                    />
                                </TableCell>
                                <TableCell class="px-4 py-2">
                                    <Checkbox
                                        :model-value="
                                            uploadSchema.state.value.columnsConfig?.[column.key]
                                                ?.optional ?? false
                                        "
                                        @update:model-value="
                                            (value) =>
                                                uploadSchema.dispatch.setColumnOptional(
                                                    column.key,
                                                    !!value,
                                                )
                                        "
                                    />
                                </TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </div>

                <ProjectUploadSchemaForm
                    :can-submit="canSubmit"
                    :loading="loading"
                    class="space-y-6 disabled:cursor-not-allowed"
                    @submit="handleUpload"
                />
            </div>
        </Transition>

        <section class="py-6" />
    </div>
</template>
