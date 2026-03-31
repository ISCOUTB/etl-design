<script setup lang="ts">
    import { filesize } from "filesize";
    import { Download, FileIcon, Rocket, X } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    const { tables, projectId } = useProjectTabsSharedState();
    const selectedFile = computed({
        get() {
            if (tables.state.value.selectedSchema) {
                return tables.state.value.selectedFiles[tables.state.value.selectedSchema.id];
            }

            return undefined;
        },
        set(value) {
            if (tables.state.value.selectedSchema) {
                tables.dispatch.setUploadedFile(tables.state.value.selectedSchema.id, value);
            }
        },
    });
    const fileURL = useObjectUrl(() => selectedFile.value?.blob);

    const config = useAppConfig();
    const { processFile } = useProjectUploadFileActions();
    function handleFile(file: File) {
        processFile(file, {
            supportedFormats: config.files.importData.supportedFormats,
            mimeTypes: config.files.importData.supportedMimeTypes,
            onError() {
                toast.error($t("errors.project.file_not_supported.title"), {
                    description: $t("errors.project.file_not_supported.description"),
                });
            },
            onSuccess(file, extension, mime) {
                if (tables.state.value.selectedSchema?.id) {
                    selectedFile.value = {
                        name: file.name,
                        nameWithoutExt: file.name.replace(/\.[^/.]+$/, ""),
                        size: filesize(file.size),
                        type: extension,
                        file,
                        blob: new Blob([file], { type: mime }),
                    };
                }
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

    function handleDrop(files: File[] | null) {
        const file = files?.[0];
        if (file) {
            handleFile(file);
        }
    }

    const errorToast = useErrorToast();
    const { handleImportData } = useProjectTableActions();
    function handleSubmit(_event: Event) {
        if (!selectedFile.value || !tables.state.value.selectedSchema) {
            return;
        }

        handleImportData(
            selectedFile.value.file,
            projectId.value,
            TableUtils.getTableName(tables.state.value.selectedSchema.import_name),
        )
            .then(() => {
                selectedFile.value = undefined;
            })
            .catch((error) => errorToast.handleServer(error));
    }
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle>{{ $t("projects.id.sections.tables.details.upload.title") }}</CardTitle>
            <CardDescription>
                {{ $t("projects.id.sections.tables.details.upload.description") }}
            </CardDescription>
        </CardHeader>
        <CardContent>
            <DropzoneArea
                :state="selectedFile"
                :supported-formats="
                    config.files.importData.supportedFormats.map((format) => `.${format}`).join(',')
                "
                @change="handleInputChange"
                @dropped="handleDrop"
            >
                <template #file-selected="{ state }">
                    <div class="space-y-4">
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
                                    @click="selectedFile = undefined"
                                >
                                    <X class="size-4" />
                                    <span class="sr-only">
                                        {{
                                            $t(
                                                "projects.id.sections.tables.details.upload.file_remove",
                                            )
                                        }}
                                    </span>
                                </Button>
                            </ItemActions>
                        </Item>
                        <div class="flex justify-end">
                            <Button variant="outline" @click="handleSubmit">
                                <Rocket />
                                {{ $t("projects.id.sections.tables.details.upload.submit") }}
                            </Button>
                        </div>
                    </div>
                </template>
            </DropzoneArea>
        </CardContent>
    </Card>
</template>
