<script setup lang="ts">
    import type { z } from "zod";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const auth = useAuth();
    const expectedConfirmation = computed(() => {
        if (!auth.data.value || !project.value?.name) {
            return;
        }

        return $t("projects.id.sections.settings.delete.validation", {
            project: project.value.name,
        });
    });

    const userInput = ref<string>("");
    const isValid = computed(() => userInput.value === expectedConfirmation.value);

    const { $localeRoute } = useNuxtApp();
    const errorToast = useErrorToast();
    const actions = useProjectActions();

    async function handleDelete() {
        if (!isValid.value || !project.value) {
            return;
        }

        actions
            .handleDeleteProject(project.value.id)
            .then(async () => {
                handleCloseModal();
                await refreshNuxtData(NuxtKeys.Projects.Search);
                await navigateTo($localeRoute({ name: "projects" }));
            })
            .catch((error) => errorToast.handleServer(error));
    }

    const modal = useModal();
    function handleCloseModal() {
        if (modal.state.value.currentModalKey === ModalKeys.Projects.Delete.ConfirmationModal) {
            modal.dispatch.setOpen(false);
        }
    }

    const { define: DefineDescription, reuse: ReuseDescription } = createReusableTemplate();
    const { define: DefineInput, reuse: ReuseInput } = createReusableTemplate();
</script>

<template>
    <DefineDescription>
        <div class="flex flex-col space-y-3">
            <i18n-t keypath="projects.id.sections.settings.delete.modal.description" tag="p">
                <template #project>
                    <strong>{{ project?.name }}</strong>
                </template>
            </i18n-t>

            <i18n-t keypath="projects.id.sections.settings.delete.modal.type_project" tag="p">
                <template #validation>
                    <code class="rounded bg-muted px-1 py-0.5 font-mono font-bold text-xs">
                        {{ expectedConfirmation }}
                    </code>
                </template>
            </i18n-t>
        </div>
    </DefineDescription>

    <DefineInput>
        <Input
            v-model="userInput"
            :placeholder="expectedConfirmation"
            autocomplete="off"
            class="font-mono text-sm"
        />
    </DefineInput>

    <ResponsiveModal desktop="alert-dialog" mobile="drawer">
        <template #alert-dialog>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>
                        {{ $t("projects.id.sections.settings.delete.modal.title") }}
                    </AlertDialogTitle>
                    <AlertDialogDescription as-child>
                        <ReuseDescription />
                    </AlertDialogDescription>

                    <div class="pt-2">
                        <ReuseInput />
                    </div>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogAction
                        :disabled="!isValid || actions.state.loading.value"
                        class="bg-destructive text-white hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                        @click="handleDelete"
                    >
                        <Spinner v-if="actions.state.loading.value" />
                        {{ $t("projects.id.sections.settings.delete.label") }}
                    </AlertDialogAction>
                    <AlertDialogCancel> {{ $t("common.actions.cancel") }} </AlertDialogCancel>
                </AlertDialogFooter>
            </AlertDialogContent>
        </template>
        <template #drawer>
            <DrawerContent>
                <DrawerHeader>
                    <DrawerTitle>
                        {{ $t("projects.id.sections.settings.delete.modal.title") }}
                    </DrawerTitle>
                    <DrawerDescription as-child>
                        <ReuseDescription />
                    </DrawerDescription>
                </DrawerHeader>

                <div class="px-4">
                    <ReuseInput />
                </div>

                <DrawerFooter>
                    <div class="flex justify-end space-x-4">
                        <Button
                            :disabled="!isValid || actions.state.loading.value"
                            class="bg-destructive text-white hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                            @click="handleDelete"
                        >
                            <Spinner v-if="actions.state.loading.value" />
                            {{ $t("projects.id.sections.settings.delete.label") }}
                        </Button>
                        <Button @click="handleCloseModal">
                            {{ $t("common.actions.cancel") }}
                        </Button>
                    </div>
                </DrawerFooter>
            </DrawerContent>
        </template>
    </ResponsiveModal>
</template>
