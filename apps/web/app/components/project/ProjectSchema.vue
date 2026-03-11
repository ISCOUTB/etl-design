<script setup lang="ts">
    import { fileTypeFromBuffer } from "file-type";
    import { filesize } from "filesize";
    import { Download, FileIcon, FileJson, FileSpreadsheet, Upload, X } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    const { uploadedFile } = useProjectTabsSharedState();

    const config = useAppConfig();
    const fileURL = useObjectUrl(() => uploadedFile.value?.blob);

    const { data: schemaExample } = useFetch<string>("/examples/schema.example.json", {
        method: "GET",
        key: NuxtKeys.Projects.Schemas.ExampleFormat,
    });

    async function processFile(file: File) {
        const bytes = new Uint8Array(await file.arrayBuffer());
        const detected = await fileTypeFromBuffer(bytes);

        const ext = (detected?.ext ?? getFileExtension(file.name)).toLowerCase();
        const mime = normalizeMime(detected?.mime ?? file.type);

        const validExt = config.files.supportedFormats.includes(ext);
        const validMime = !mime.length || config.files.supportedMimeTypes.includes(mime);

        if (!validExt || !validMime) {
            toast.error($t("errors.project.file_not_supported.title"), {
                description: $t("errors.project.file_not_supported.description"),
            });

            return;
        }

        uploadedFile.value = {
            name: file.name,
            size: filesize(file.size),
            type: ext,
            blob: new Blob([file], { type: mime }),
        };
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
                :state="uploadedFile"
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
                                    @click="uploadedFile = undefined"
                                >
                                    <X class="size-4" />
                                </Button>
                            </ItemActions>
                        </Item>

                        <div class="mt-6 flex justify-end">
                            <Button>
                                <Upload />
                                <span>
                                    {{ $t("projects.id.sections.schema.events.upload_file.label") }}
                                </span>
                            </Button>
                        </div>
                    </div>
                </template>
            </DropzoneArea>
        </section>

        <section>
            <h3 class="mb-1 text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.schema.expected_json.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.schema.expected_json.description") }}
            </p>

            <CodeBlock
                :content="schemaExample"
                :file="$t('projects.id.sections.schema.expected_json.example_filename')"
            />
        </section>
    </div>
</template>
