<script setup lang="ts">
    import type { z } from "zod";
    import { fileTypeFromBuffer } from "file-type";
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

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const events = useAppEvents();

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
            file,
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

    const animations = useProjectSchemaAnimations();
    const modal = useModal();
    const canSubmit = computed<boolean>(() => {
        const uploaded = schema.state.value.uploadedFile;
        const hasFile = !!uploaded && uploaded.blob.size > 0;
        const hasValidTableName = (schema.state.value.tableName?.trim().length ?? 0) > 0;
        const hasErrors = schema.errors.value.length > 0;

        return hasFile && hasValidTableName && !hasErrors;
    });

    function handleUpload(_event: Event) {
        modal.dispatch.loadComponent({
            loader: () =>
                import("~/components/project/schema/ProjectSchemaUploadConfirmationModal.vue"),
            key: ModalKeys.Projects.Schema.UploadFile,
            kind: "alert-dialog",
            props: {
                project,
            },
        });

        if (modal.state.value.currentModalKey === ModalKeys.Projects.Schema.UploadFile) {
            modal.dispatch.setOpen(true);
        }
    }

    onMounted(() => {
        events.on("event:schema:table-created", () => {
            schema.dispatch.setUploadedFile(undefined);
        });
    });
</script>

<template>
    <div class="space-y-4">
        <section class="space-y-4">
            <div class="space-y-1">
                <h3 class="text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.schema.header.title") }}
                </h3>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.schema.header.description") }}
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
            </div>
        </section>

        <Transition
            appear
            mode="out-in"
            @enter="animations.onSchemaEnter"
            @leave="animations.onSchemaLeave"
        >
            <div v-if="shouldShowExample">
                <ProjectSchemaFields
                    v-if="schema.state.value.uploadedFile"
                    :can-submit="canSubmit"
                    class="space-y-6"
                    @submit="handleUpload"
                />

                <ProjectSchemaExample />
            </div>
            <div v-else class="space-y-6">
                <div v-if="schema.errors.value.length > 0">
                    <Alert variant="destructive">
                        <TriangleAlert />
                        <AlertTitle>Warnings</AlertTitle>
                        <AlertDescription>
                            <ul class="list-inside list-disc space-y-1">
                                <li v-for="error in schema.errors.value" :key="error.key">
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
                        {{ $t("projects.id.sections.schema.datatype_table.title") }}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        {{ $t("projects.id.sections.schema.datatype_table.description") }}
                    </p>
                </div>

                <div class="rounded-lg border overflow-hidden">
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
                                <TableHead> Primary </TableHead>
                                <TableHead> Unique </TableHead>
                                <TableHead> Optional </TableHead>
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
                                <TableCell class="px-4 py-2">
                                    <Checkbox
                                        :disabled="
                                            Object.entries(schema.state.value.columnsConfig).some(
                                                ([k, v]) => v.primary_key && k !== column.key,
                                            )
                                        "
                                        :model-value="
                                            schema.state.value.columnsConfig?.[column.key]
                                                ?.primary_key ?? false
                                        "
                                        @update:model-value="
                                            (value) =>
                                                schema.dispatch.setColumnPrimaryKey(
                                                    column.key,
                                                    !!value,
                                                )
                                        "
                                    />
                                </TableCell>
                                <TableCell class="px-4 py-2">
                                    <Checkbox
                                        :model-value="
                                            schema.state.value.columnsConfig?.[column.key]
                                                ?.unique ?? false
                                        "
                                        @update:model-value="
                                            (value) =>
                                                schema.dispatch.setColumnUnique(column.key, !!value)
                                        "
                                    />
                                </TableCell>
                                <TableCell class="px-4 py-2">
                                    <Checkbox
                                        :model-value="
                                            schema.state.value.columnsConfig?.[column.key]
                                                ?.optional ?? false
                                        "
                                        @update:model-value="
                                            (value) =>
                                                schema.dispatch.setColumnOptional(
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

                <ProjectSchemaFields
                    :can-submit="canSubmit"
                    class="space-y-6 disabled:cursor-not-allowed"
                    @submit="handleUpload"
                />
            </div>
        </Transition>

        <section class="py-6" />
    </div>
</template>
