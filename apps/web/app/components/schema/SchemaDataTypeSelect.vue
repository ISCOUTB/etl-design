<script setup lang="ts">
    import type { DtypesEnum } from "#shared/utils/schemas/api";
    import type { Component, HTMLAttributes } from "vue";
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

    const [DefineTemplate, ReuseTemplate] = createReusableTemplate<{ icon: Component }>();

    const items = computed<DataType[]>(() => [
        {
            label: $t("projects.id.sections.schema.datatype_table.datatype.string"),
            value: "string",
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
    <DefineTemplate v-slot="{ icon }">
        <div class="flex size-6 items-center justify-center rounded">
            <component :is="icon" class="size-3.5" />
        </div>
    </DefineTemplate>

    <Select v-model:model-value="model">
        <SelectTrigger :class="cn('w-48', props.class)">
            <div class="flex items-center space-x-2">
                <ReuseTemplate
                    :icon="TableUtils.getIcon((model || 'string') as Dtype)"
                    :class="cn(TableUtils.getColor(model as Dtype | undefined))"
                />
                <SelectValue
                    :placeholder="$t('projects.id.sections.schema.datatype_table.header.data_type')"
                />
            </div>
        </SelectTrigger>
        <SelectContent>
            <SelectItem v-for="item in items" :key="item.value" :value="item.value">
                <ReuseTemplate
                    :icon="TableUtils.getIcon(item.value)"
                    :class="cn(TableUtils.getColor(item.value))"
                />
                {{ item.label }}
            </SelectItem>
        </SelectContent>
    </Select>
</template>
