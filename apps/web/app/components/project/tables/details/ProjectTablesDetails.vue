<script setup lang="ts">
    import { filesize } from "filesize";
    import { ArrowLeft, Download, FileIcon, Pencil, Table2, Trash2, X } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    const { project, tables } = useProjectTabsSharedState();

    const tableName = computed(() => {
        if (!tables.state.value.selectedSchema) {
            return;
        }

        return TableUtils.getTableName(tables.state.value.selectedSchema.import_name);
    });

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

    const events = useAppEvents();
    function handleBack(_event: Event) {
        events.emit("event:projects:table:change-view", { value: "list" });
    }

    const modal = useModal();

    const config = useAppConfig();
    const actions = useProjectUploadFileActions();
    function handleFile(file: File) {
        actions.processFile(file, {
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

    function handleDelete(_event: Event) {
        if (!project.value) {
            return;
        }

        modal.dispatch.loadComponent({
            loader: () => import("~/components/project/tables/ProjectTablesDeleteModal.vue"),
            key: ModalKeys.Projects.Tables.Delete,
            props: {
                table: tables.state.value.selectedSchema,
                projectId: project.value.id,
                kind: "delete",
                onSuccess: () => {
                    events.emit("event:projects:table:change-view", { value: "list" });
                    tables.dispatch.setSelectedSchema(undefined);
                },
            },
        });
    }
</script>

<template>
    <div>
        <div class="flex flex-col space-y-6">
            <div class="flex items-center gap-4">
                <Button variant="ghost" size="icon" class="shrink-0" @click="handleBack">
                    <ArrowLeft class="size-4" />
                    <span class="sr-only">Back to tables</span>
                </Button>
                <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-3">
                        <div
                            class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10"
                        >
                            <Table2 class="size-5 text-primary" />
                        </div>
                        <div>
                            <h2 class="text-lg font-medium text-foreground">
                                {{ tableName }}
                            </h2>
                            <p class="text-xs text-muted-foreground font-mono">
                                {{ tables.state.value.selectedSchema?.id }}
                            </p>
                        </div>
                    </div>
                </div>

                <div class="space-x-2">
                    <Button v-if="project" variant="outline" as-child>
                        <NuxtLink
                            :to="
                                $localePath({
                                    name: 'projects-id-tables-tableName-edit',
                                    params: { id: project.id, tableName },
                                    query: {
                                        callbackUrl: $route.fullPath,
                                    },
                                })
                            "
                        >
                            <Pencil class="size-4" />
                            Edit Schema
                        </NuxtLink>
                    </Button>
                    <Button
                        v-if="tables.state.value.selectedSchema"
                        variant="destructive"
                        :disabled="tables.state.value.selectedSchema.schemas_releases.length > 0"
                        @click="handleDelete"
                    >
                        <Trash2 class="size-4" />
                    </Button>
                </div>
            </div>

            <ProjectTablesDetailsOverview />

            <Card>
                <CardHeader>
                    <CardTitle> Import Data </CardTitle>
                    <CardDescription>
                        Select a file to import records into your database
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <DropzoneArea
                        :state="selectedFile"
                        :supported-formats="
                            config.files.importData.supportedFormats
                                .map((format) => `.${format}`)
                                .join(',')
                        "
                        @change="handleInputChange"
                        @dropped="handleDrop"
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
                                            @click="selectedFile = undefined"
                                        >
                                            <X class="size-4" />
                                        </Button>
                                    </ItemActions>
                                </Item>
                            </div>
                        </template>
                    </DropzoneArea>
                </CardContent>
            </Card>

            <ProjectTablesDetailsVersionHistory />
        </div>
    </div>
</template>
