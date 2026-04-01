<script setup lang="ts">
    import { Upload } from "lucide-vue-next";

    interface Props {
        canSubmit: MaybeRefOrGetter<boolean>;
    }

    interface Emits {
        submit: [event: Event];
    }

    const props = defineProps<Props>();

    const emit = defineEmits<Emits>();

    const canSubmit = computed(() => toValue(props.canSubmit));

    const { uploadSchema } = useProject();

    const tableName = computed<string>({
        get: () => {
            const name = uploadSchema.state.value.tableName;
            if (name !== undefined) {
                return name;
            }

            return uploadSchema.state.value.uploadedFile?.nameWithoutExt ?? "";
        },
        set: (value) => uploadSchema.dispatch.setTableName(value),
    });

    function handleSubmit(event: Event) {
        emit("submit", event);
    }
</script>

<template>
    <div>
        <div>
            <h3 className="mb-1 text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.upload_schema.table_name.title") }}
            </h3>
            <p className="mb-4 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.upload_schema.table_name.description") }}
            </p>

            <Field>
                <Input
                    v-model="tableName"
                    type="text"
                    :default-value="uploadSchema.state.value.uploadedFile?.nameWithoutExt"
                    :aria-invalid="!tableName.trim()"
                    :placeholder="$t('projects.id.sections.upload_schema.table_name.placeholder')"
                />
                <FieldError
                    v-if="!tableName.trim()"
                    :errors="[
                        $t('projects.id.sections.upload_schema.validation.table_name_not_empty'),
                    ]"
                />
            </Field>
        </div>

        <div class="flex justify-end space-x-2">
            <Button
                type="button"
                variant="ghost"
                class="cursor-pointer"
                :disabled="!canSubmit"
                @click="handleSubmit"
            >
                <Upload />
                <span>
                    {{ $t("projects.id.sections.upload_schema.events.upload_file.label") }}
                </span>
            </Button>

            <Button type="button" variant="destructive" @click="$router.back()">
                {{ $t("common.actions.cancel") }}
            </Button>
        </div>
    </div>
</template>
