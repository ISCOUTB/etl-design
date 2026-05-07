<script setup lang="ts">
    import { WandSparkles, X } from "lucide-vue-next";
    import { z } from "zod";

    interface Props {
        onSubmit: (userMessage: string) => void;
    }

    const props = defineProps<Props>();

    const Schema = computed(() =>
        z.object({
            message: z.string().min(1, {
                error: $t("common.validation.required"),
            }),
        }),
    );

    const { handleSubmit } = useForm({
        validationSchema: toTypedSchema(Schema.value),
        initialValues: {
            message: "",
        },
    });

    const onSubmit = handleSubmit((values) => {
        props.onSubmit(values.message);
        handleClose();
    });
    const [DefineForm, ReuseForm] = createReusableTemplate();

    const modal = useModal();
    function handleClose() {
        if (modal.state.value.currentModalKey === ModalKeys.Projects.QueryBuilder.Generate) {
            modal.dispatch.setOpen(false);
        }
    }
</script>

<template>
    <DefineForm>
        <form class="flex flex-col space-y-4" @submit="onSubmit">
            <VeeField v-slot="{ field, errors }" name="message">
                <Field>
                    <FieldLabel>
                        {{
                            $t(
                                "projects.id.sections.query_builder.generate.modal.form.message.label",
                            )
                        }}
                    </FieldLabel>
                    <Textarea
                        id="message"
                        v-bind="field"
                        v-model:model-value="field.value"
                        class="h-32 resize-none"
                        :placeholder="
                            $t(
                                'projects.id.sections.query_builder.generate.modal.form.message.placeholder',
                            )
                        "
                    />
                    <FieldError v-if="errors.length" :errors="errors" />
                </Field>
            </VeeField>

            <div class="flex justify-end space-x-2">
                <Button type="submit" variant="outline" class="cursor-pointer">
                    <WandSparkles />
                    {{ $t("projects.id.sections.query_builder.generate.modal.actions.generate") }}
                </Button>
                <Button
                    type="button"
                    variant="secondary"
                    class="cursor-pointer"
                    @click="handleClose"
                >
                    <X />
                    {{ $t("projects.id.sections.query_builder.generate.modal.actions.cancel") }}
                </Button>
            </div>
        </form>
    </DefineForm>

    <ResponsiveModal desktop="dialog" mobile="drawer">
        <template #dialog>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>
                        {{ $t("projects.id.sections.query_builder.generate.modal.title") }}
                    </DialogTitle>
                    <DialogDescription>
                        {{ $t("projects.id.sections.query_builder.generate.modal.description") }}
                    </DialogDescription>
                </DialogHeader>

                <ReuseForm />
            </DialogContent>
        </template>
        <template #drawer>
            <DrawerContent>
                <DrawerHeader>
                    <DrawerTitle>
                        {{ $t("projects.id.sections.query_builder.generate.modal.title") }}
                    </DrawerTitle>
                    <DrawerDescription>
                        {{ $t("projects.id.sections.query_builder.generate.modal.description") }}
                    </DrawerDescription>

                    <ReuseForm />
                </DrawerHeader>
            </DrawerContent>
        </template>
    </ResponsiveModal>
</template>
