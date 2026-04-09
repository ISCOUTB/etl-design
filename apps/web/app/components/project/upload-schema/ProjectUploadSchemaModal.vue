<script setup lang="ts">
    import type { z } from "zod";
    import { Upload } from "lucide-vue-next";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
        onSubmit: () => void;
    }

    const props = defineProps<Props>();
    const actions = useProjectTableActions();

    function handleSubmit(_event: Event) {
        props.onSubmit();
    }

    const modal = useModal();
    function handleCloseModal() {
        if (modal.state.value.currentModalKey === ModalKeys.Projects.Schema.UploadSchema) {
            modal.dispatch.setOpen(false);
        }
    }
</script>

<template>
    <ResponsiveModal desktop="alert-dialog" mobile="drawer">
        <template #alert-dialog>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>
                        {{ $t("projects.id.sections.upload_schema.upload.title") }}
                    </AlertDialogTitle>
                    <AlertDialogDescription>
                        {{ $t("projects.id.sections.upload_schema.upload.description") }}
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogAction
                        :disabled="actions.state.loading.value"
                        class="space-x-2"
                        @click="handleSubmit"
                    >
                        <Upload />
                        {{ $t("projects.id.sections.upload_schema.events.upload_file.label") }}
                    </AlertDialogAction>
                    <AlertDialogCancel> {{ $t("common.actions.cancel") }} </AlertDialogCancel>
                </AlertDialogFooter>
            </AlertDialogContent>
        </template>
        <template #drawer>
            <DrawerContent>
                <DrawerHeader>
                    <DrawerTitle>
                        {{ $t("projects.id.sections.upload_schema.upload.title") }}
                    </DrawerTitle>
                    <DrawerDescription>
                        {{ $t("projects.id.sections.upload_schema.upload.description") }}
                    </DrawerDescription>
                </DrawerHeader>

                <DrawerFooter>
                    <div class="flex justify-end space-x-4">
                        <Button
                            :disabled="actions.state.loading.value"
                            class="space-x-2"
                            @click="handleSubmit"
                        >
                            <Upload />
                            {{ $t("projects.id.sections.upload_schema.events.upload_file.label") }}
                        </Button>
                        <Button variant="outline" @click="handleCloseModal">
                            {{ $t("common.actions.cancel") }}
                        </Button>
                    </div>
                </DrawerFooter>
            </DrawerContent>
        </template>
    </ResponsiveModal>
</template>
