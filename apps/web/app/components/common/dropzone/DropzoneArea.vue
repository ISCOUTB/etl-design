<script setup lang="ts" generic="TState">
    import type { UseDropZoneOptions } from "@vueuse/core";
    import { Upload } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface Props<T> {
        state: MaybeRefOrGetter<T | undefined>;
        disabled?: MaybeRefOrGetter<boolean>;
        supportedFormats?: string;
        dropzoneOptions?: UseDropZoneOptions;
    }

    interface Emits {
        dropped: [files: File[] | null];
        change: [event: Event];
    }

    const props = withDefaults(defineProps<Props<TState>>(), {
        dropzoneOptions: () => ({ preventDefaultForUnhandled: true }),
    });
    const emit = defineEmits<Emits>();

    const state = computed(() => toValue(props.state));

    const dropzone = useTemplateRef<HTMLElement>("dropzone");
    const { isOverDropZone } = useDropZone(dropzone, {
        onDrop: (files) => {
            emit("dropped", files);
        },
        onOver: (_, event) => {
            event.preventDefault();
            if (event.dataTransfer) {
                event.dataTransfer.dropEffect = "copy";
            }
        },
        onLeave: (_, event) => {
            event.preventDefault();
        },
        preventDefaultForUnhandled: true,
        ...props.dropzoneOptions,
    });

    const disabled = computed(() => toValue(props.disabled));
    const animations = useSchemaUploadAnimation();

    function handleChange(event: Event) {
        emit("change", event);
    }

    onMounted(() => {
        whenever(isOverDropZone, (flag) => {
            animations.animateDropzoneHover(dropzone.value, flag);
        });
    });
</script>

<template>
    <Transition
        mode="out-in"
        appear
        @enter="animations.onUploadStateEnter"
        @leave="animations.onUploadStateLeave"
    >
        <template v-if="!state">
            <div class="space-y-4">
                <Label
                    ref="dropzone"
                    :class="
                        cn(
                            'relative min-h-80 cursor-pointer flex flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors',
                            isOverDropZone
                                ? 'border-primary bg-primary/5'
                                : 'border-muted-foreground/25 hover:border-muted-foreground/50',
                            disabled &&
                                'opacity-60 cursor-not-allowed pointer-events-none grayscale-[0.5] border-muted',
                        )
                    "
                >
                    <Input
                        type="file"
                        :disabled="disabled"
                        class="sr-only"
                        :accept="supportedFormats"
                        @change="handleChange"
                    />

                    <div
                        :class="
                            cn(
                                'flex flex-col items-center gap-3 text-center',
                                disabled && 'select-none opacity-50',
                            )
                        "
                    >
                        <slot name="dropzone-content">
                            <div
                                class="flex size-12 items-center justify-center rounded-full bg-muted"
                            >
                                <Upload class="size-5 text-muted-foreground" />
                            </div>
                            <div>
                                <p class="text-sm font-medium text-foreground">
                                    {{ $t("projects.id.sections.upload_schema.dropzone.title") }}
                                    <span class="text-primary">
                                        {{
                                            $t("projects.id.sections.upload_schema.dropzone.browse")
                                        }}
                                    </span>
                                </p>
                                <p class="mt-1 text-xs text-muted-foreground">
                                    <i18n-t
                                        keypath="projects.id.sections.upload_schema.dropzone.supported"
                                    >
                                        <template #formats>
                                            <span class="font-bold">
                                                {{ supportedFormats }}
                                            </span>
                                        </template>
                                    </i18n-t>
                                </p>
                            </div>
                        </slot>
                    </div>
                </Label>

                <div v-if="disabled">
                    <slot name="disabled" />
                </div>
            </div>
        </template>

        <template v-else>
            <slot name="file-selected" v-bind="{ state }" />
        </template>
    </Transition>
</template>
