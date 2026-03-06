<script setup lang="ts">
    import type { z } from "zod";
    import { fileTypeFromBuffer } from "file-type";
    import { filesize } from "filesize";
    import { FileIcon, FileJson, FileSpreadsheet, Upload, X } from "lucide-vue-next";
    import { toast } from "vue-sonner";
    import { cn } from "~/lib/utils";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    interface UploadedFile {
        name: string;
        size: number;
        formattedSize: string;
        type: string;
        raw: File;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const config = useAppConfig();
    const uploadedFile = useState<UploadedFile | undefined>(
        NuxtKeys.Projects.UploadFile(project.value),
        () => undefined,
    );

    const dropzone = useTemplateRef<HTMLElement>("dropzoneRef");
    const { isOverDropZone } = useDropZone(dropzone, {
        onDrop: (files) => {
            const file = files?.[0];
            if (file) {
                processFile(file);
            }
        },
        dataTypes: config.files.supportedMimeTypes,
        multiple: false,
        preventDefaultForUnhandled: true,
    });

    const { data: schemaExample } = useFetch<string>("/examples/schema.example.json", {
        method: "GET",
        key: NuxtKeys.Projects.Schemas.ExampleFormat,
    });

    async function processFile(file: File) {
        const bytes = new Uint8Array(await file.arrayBuffer());
        const fileType = await fileTypeFromBuffer(bytes);
        if (!fileType) {
            return;
        }

        const validFile =
            config.files.supportedFormats.includes(fileType.ext) &&
            config.files.supportedMimeTypes.includes(fileType.mime);

        if (validFile) {
            uploadedFile.value = {
                name: file.name,
                size: file.size,
                formattedSize: filesize(file.size),
                type: fileType.ext,
                raw: file,
            };

            return;
        }

        toast.error($t("errors.project.file_not_supported.title"), {
            description: $t("errors.project.file_not_supported.description"),
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

            <Label
                v-if="!uploadedFile"
                ref="dropzoneRef"
                :class="
                    cn(
                        'relative min-h-80 cursor-pointer flex flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors',
                        isOverDropZone
                            ? 'border-primary bg-primary/5'
                            : 'border-muted-foreground/25 hover:border-muted-foreground/50',
                    )
                "
            >
                <Input
                    type="file"
                    class="sr-only"
                    :accept="config.files.supportedFormats.map((format) => `.${format}`).join(',')"
                    @change="handleInputChange"
                />

                <div class="flex flex-col items-center gap-3 text-center">
                    <div class="flex size-12 items-center justify-center rounded-full bg-muted">
                        <Upload class="size-5 text-muted-foreground" />
                    </div>
                    <div>
                        <p class="text-sm font-medium text-foreground">
                            {{ $t("projects.id.sections.schema.dropzone.title") }}
                            <span class="text-primary">
                                {{ $t("projects.id.sections.schema.dropzone.browse") }}
                            </span>
                        </p>
                        <p class="mt-1 text-xs text-muted-foreground">
                            <i18n-t keypath="projects.id.sections.schema.dropzone.supported">
                                <template #formats>
                                    <span class="font-bold">
                                        {{
                                            config.files.supportedFormats
                                                .map((format) => `.${format}`)
                                                .join(",")
                                        }}
                                    </span>
                                </template>
                            </i18n-t>
                        </p>
                    </div>
                </div>
            </Label>

            <template v-else>
                <Item variant="outline">
                    <ItemMedia>
                        <div class="bg-emerald-500/10 p-2 rounded-md">
                            <FileIcon class="size-5 text-emerald-500" />
                        </div>
                    </ItemMedia>
                    <ItemContent>
                        <ItemTitle class="truncate font-medium text-foreground">
                            {{ uploadedFile.name }}
                        </ItemTitle>
                        <ItemDescription>
                            {{ uploadedFile.formattedSize }}
                        </ItemDescription>
                    </ItemContent>
                    <ItemActions>
                        <Button variant="ghost" size="icon" @click="uploadedFile = undefined">
                            <X class="size-4" />
                        </Button>
                    </ItemActions>
                </Item>

                <div class="mt-6 flex justify-end">
                    <Button>
                        <Upload />
                        <span>{{ $t('projects.id.sections.schema.events.upload_file.label') }}</span>
                    </Button>
                </div>
            </template>
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
