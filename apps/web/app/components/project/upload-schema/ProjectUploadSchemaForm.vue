<script setup lang="ts">
    import { Check } from "lucide-vue-next";

    interface Props {
        canSubmit: MaybeRefOrGetter<boolean>;
        loading: MaybeRefOrGetter<boolean>;
    }

    interface Emits {
        submit: [event: Event];
    }

    const props = defineProps<Props>();
    const emit = defineEmits<Emits>();

    const canSubmit = computed(() => toValue(props.canSubmit));
    const loading = computed(() => toValue(props.loading));

    const { uploadSchema } = useProject();
    const { $logger } = useNuxtApp();

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

    const insertData = computed({
        get: () => uploadSchema.state.value.insertData,
        set: (value) => uploadSchema.dispatch.setInsertData(value),
    });

    function handleSubmit(event: Event) {
        $logger.info(tableName.value, insertData.value);
        emit("submit", event);
    }
</script>

<template>
    <div>
        <div class="space-y-4">
            <div class="space-y-1">
                <h3 class="text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.upload_schema.table_name.title") }}
                </h3>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.upload_schema.table_name.description") }}
                </p>
            </div>

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

        <div v-if="uploadSchema.computed.isTabular.value" class="space-y-4">
            <h3 class="text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.upload_schema.form.additional_configurations") }}
            </h3>
            <Field orientation="horizontal">
                <Checkbox id="insert-data" v-model:model-value="insertData" />
                <FieldContent>
                    <FieldLabel for="insert-data">
                        {{ $t("projects.id.sections.upload_schema.form.insert_data.label") }}
                    </FieldLabel>
                    <FieldContent>
                        {{ $t("projects.id.sections.upload_schema.form.insert_data.description") }}
                    </FieldContent>
                </FieldContent>
            </Field>
        </div>

        <div class="flex justify-end space-x-2">
            <Button
                type="button"
                variant="ghost"
                class="cursor-pointer"
                :disabled="!canSubmit || loading"
                @click="handleSubmit"
            >
                <UtilsLoading :loading="loading">
                    <Check />
                </UtilsLoading>
                <span>
                    {{ $t("projects.id.sections.upload_schema.events.upload_file.confirmation") }}
                </span>
            </Button>

            <Button
                type="button"
                variant="destructive"
                @click="uploadSchema.dispatch.setUploadedFile(undefined)"
            >
                {{ $t("common.actions.cancel") }}
            </Button>
        </div>
    </div>
</template>
