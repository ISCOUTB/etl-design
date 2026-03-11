<script setup lang="ts">
    interface Props {
        defaultValue?: string;
        modelValue?: string;
    }

    interface Emits {
        "update:modelValue": [payload: string];
    }

    interface DataType {
        label: string;
        value: string;
    }

    const props = defineProps<Props>();
    const emits = defineEmits<Emits>();

    const model = useVModel(props, "modelValue", emits, {
        passive: true,
        defaultValue: props.defaultValue,
    });

    const items = computed<DataType[]>(() => [
        {
            label: $t("projects.id.sections.schema.datatype_table.datatype.text"),
            value: "text",
        },
        {
            label: $t("projects.id.sections.schema.datatype_table.datatype.int"),
            value: "integer",
        },
        {
            label: $t("projects.id.sections.schema.datatype_table.datatype.float"),
            value: "float",
        },
        {
            label: $t("projects.id.sections.schema.datatype_table.datatype.double"),
            value: "double",
        },
        {
            label: $t("projects.id.sections.schema.datatype_table.datatype.boolean"),
            value: "boolean",
        },
    ]);
</script>

<template>
    <Select v-model:model-value="model">
        <SelectTrigger class="w-48">
            <SelectValue
                :placeholder="$t('projects.id.sections.schema.datatype_table.header.data_type')"
            />
        </SelectTrigger>
        <SelectContent>
            <SelectItem v-for="item in items" :key="item.value" :value="item.value">
                {{ item.label }}
            </SelectItem>
        </SelectContent>
    </Select>
</template>
