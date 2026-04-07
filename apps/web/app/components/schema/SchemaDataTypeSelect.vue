<script setup lang="ts">
    import type { DtypesEnum } from "#shared/utils/schemas/api";
    import type { HTMLAttributes } from "vue";
    import type z from "zod";
    import { cn } from "~/lib/utils";

    interface Props {
        defaultValue?: string;
        modelValue?: string;
        class?: HTMLAttributes["class"];
    }

    interface Emits {
        "update:modelValue": [payload: string];
    }

    interface DataType {
        label: string;
        value: z.infer<typeof DtypesEnum>;
    }

    const props = defineProps<Props>();
    const emits = defineEmits<Emits>();

    const model = useVModel(props, "modelValue", emits, {
        passive: true,
        defaultValue: props.defaultValue,
    });

    const resolvedModel = computed<Dtype>(() => {
        return (model.value || "string") as Dtype;
    });

    const items = computed<DataType[]>(() => [
        {
            label: $t("projects.id.sections.upload_schema.datatype_table.datatype.string"),
            value: "string",
        },
        {
            label: $t("projects.id.sections.upload_schema.datatype_table.datatype.int"),
            value: "integer",
        },
        {
            label: $t("projects.id.sections.upload_schema.datatype_table.datatype.float"),
            value: "float",
        },
        {
            label: $t("projects.id.sections.upload_schema.datatype_table.datatype.double"),
            value: "double",
        },
        {
            label: $t("projects.id.sections.upload_schema.datatype_table.datatype.boolean"),
            value: "boolean",
        },
    ]);
</script>

<template>
    <Select v-model:model-value="model">
        <SelectTrigger :class="cn('w-48', props.class)">
            <div class="flex items-center">
                <SchemaDtype :dtype="resolvedModel">
                    <template #icon>
                        <component :is="TableUtils.getIcon(resolvedModel)" />
                    </template>
                </SchemaDtype>
                <SelectValue
                    :placeholder="
                        $t('projects.id.sections.upload_schema.datatype_table.header.data_type')
                    "
                />
            </div>
        </SelectTrigger>
        <SelectContent :body-lock="false">
            <SelectItem v-for="item in items" :key="item.value" :value="item.value">
                <SchemaDtype :dtype="item.value">
                    <template #icon>
                        <component :is="TableUtils.getIcon(item.value)" />
                    </template>
                    {{ item.label }}
                </SchemaDtype>
            </SelectItem>
        </SelectContent>
    </Select>
</template>
