<script setup lang="ts">
    import type { z } from "zod";
    import { fileTypeFromBuffer } from "file-type";
    import { filesize } from "filesize";
    import { Download, FileIcon, FileJson, FileSpreadsheet, Upload, X } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const { schema } = useProjectTabsSharedState();

    const config = useAppConfig();
    const fileURL = useObjectUrl(() => schema.state.value.uploadedFile?.blob);
    const shouldShowExample = computed(
        () =>
            !schema.state.value.uploadedFile ||
            (schema.state.value.uploadedFile && schema.state.value.uploadedFile.type === "json"),
    );

    async function processFile(file: File) {
        const bytes = new Uint8Array(await file.arrayBuffer());
        const detected = await fileTypeFromBuffer(bytes);

        const ext = (detected?.ext ?? SchemaUtils.File.getFileExtension(file.name)).toLowerCase();
        const mime = SchemaUtils.File.normalizeMime(detected?.mime ?? file.type);

        const validExt = config.files.supportedFormats.includes(ext);
        const validMime = !mime.length || config.files.supportedMimeTypes.includes(mime);

        if (!validExt || !validMime) {
            toast.error($t("errors.project.file_not_supported.title"), {
                description: $t("errors.project.file_not_supported.description"),
            });

            return;
        }

        schema.dispatch.setUploadedFile({
            name: file.name,
            nameWithoutExt: file.name.replace(/\.[^/.]+$/, ""),
            size: filesize(file.size),
            type: ext,
            blob: new Blob([file], { type: mime }),
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

        processFile(file);
    }

    const dataTypeModels = computed(() =>
        Object.fromEntries(
            schema.computed.columns.value.map((column) => [
                String(column.key),
                schema.dispatch.getColumnDataTypeModel(String(column.key)),
            ]),
        ),
    );

    const tableName = computed<string>({
        get: () =>
            schema.state.value.tableName?.trim() ||
            schema.state.value.uploadedFile?.nameWithoutExt ||
            "",
        set: (value) => schema.dispatch.setTableName(value),
    });

    const animations = useProjectSchemaAnimations();
    const modal = useModal();

    function handleUpload(_event: Event) {
        modal.loadComponent({
            loader: () => import("@/components/project/ProjectSchemaUploadConfirmationModal.vue"),
            key: ModalKeys.Projects.Schema.UploadFile,
            props: {
                project,
            },
        });

        if (modal.currentModalKey.value === ModalKeys.Projects.Schema.UploadFile) {
            modal.open.value = true;
        }
    }
</script>

<template>
    <div class="flex flex-col gap-8">
        <section>
            <h3 class="mb-1 text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.schema.header.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.schema.header.description") }}
            </p>

            <div class="mb-6 grid gap-4 sm:grid-cols-2">
                <Item variant="outline">
                    <ItemMedia>
                        <div class="bg-emerald-500/10 p-2 rounded-md">
                            <FileSpreadsheet class="size-5 text-emerald-500" />
                        </div>
                    </ItemMedia>
                    <ItemContent>
                        <ItemTitle class="font-medium text-foreground"> Excel / CSV </ItemTitle>
                        <ItemDescription>
                            {{ $t("projects.id.sections.schema.cards.supported_formats") }}
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
                            {{ $t("projects.id.sections.schema.cards.json_schema") }}
                        </ItemTitle>
                        <ItemDescription>
                            {{ $t("projects.id.sections.schema.cards.upload_json") }}
                        </ItemDescription>
                    </ItemContent>
                </Item>
            </div>

            <DropzoneArea
                :state="() => schema.state.value.uploadedFile"
                :supported-formats="
                    config.files.supportedFormats.map((format) => `.${format}`).join(',')
                "
                :dropzone-options="{ multiple: false }"
                @dropped="
                    (files) => {
                        const file = files?.[0];
                        if (file) {
                            processFile(file);
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
                                    @click="schema.dispatch.setUploadedFile(undefined)"
                                >
                                    <X class="size-4" />
                                </Button>
                            </ItemActions>
                        </Item>
                    </div>
                </template>
            </DropzoneArea>
        </section>

        <Transition
            appear
            mode="out-in"
            @enter="animations.onSchemaEnter"
            @leave="animations.onSchemaLeave"
        >
            <ProjectSchemaExample v-if="shouldShowExample" />
            <div v-else>
                <h3 className="mb-1 text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.schema.datatype_table.title") }}
                </h3>
                <p className="mb-4 text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.schema.datatype_table.description") }}
                </p>

                <div class="rounded-lg border border-amber-300/70 overflow-hidden">
                    <Table>
                        <TableHeader>
                            <TableRow class="hover:bg-amber-300/30">
                                <TableHead class="p-4">
                                    {{
                                        $t(
                                            "projects.id.sections.schema.datatype_table.header.column",
                                        )
                                    }}
                                </TableHead>
                                <TableHead class="p-4">
                                    {{
                                        $t(
                                            "projects.id.sections.schema.datatype_table.header.sample_value",
                                        )
                                    }}
                                </TableHead>
                                <TableHead class="p-4">
                                    {{
                                        $t(
                                            "projects.id.sections.schema.datatype_table.header.data_type",
                                        )
                                    }}
                                </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            <TableRow
                                v-for="column in schema.computed.columns.value"
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
                                        {{ schema.computed.sampleValueByColumn.value[column.key] }}
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
                            </TableRow>
                        </TableBody>
                    </Table>
                </div>

                <div class="mt-6">
                    <h3 className="mb-1 text-sm font-medium text-foreground">
                        {{ $t("projects.id.sections.schema.table_name.title") }}
                    </h3>
                    <p className="mb-4 text-sm text-muted-foreground">
                        {{ $t("projects.id.sections.schema.table_name.description") }}
                    </p>

                    <Input
                        v-model="tableName"
                        type="text"
                        :default-value="schema.state.value.uploadedFile?.nameWithoutExt"
                        :placeholder="$t('projects.id.sections.schema.table_name.placeholder')"
                    />
                </div>

                <div class="mt-4 flex justify-end space-x-2">
                    <Button
                        type="button"
                        variant="ghost"
                        class="cursor-pointer"
                        @click="handleUpload"
                    >
                        <Upload />
                        <span>
                            {{ $t("projects.id.sections.schema.events.upload_file.label") }}
                        </span>
                    </Button>

                    <Button type="button" variant="destructive" @click="$router.back()">
                        {{ $t("common.actions.cancel") }}
                    </Button>
                </div>
            </div>
        </Transition>

        <section class="py-6" />
    </div>
</template>
