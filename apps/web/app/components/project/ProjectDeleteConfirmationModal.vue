<script setup lang="ts">
    import type { z } from "zod";
    import { FetchError } from "ofetch";

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

    const userInput = useState(NuxtKeys.Projects.Delete.Validation(project.value), () => "");
    const isValid = computed(() => userInput.value === expectedConfirmation.value);

    const { $localeRoute } = useNuxtApp();
    const api = useApi();
    const errorToast = useErrorToast();
    async function handleDelete() {
        if (!isValid.value || !project.value) {
            return;
        }

        try {
            await api(`/projects/${project.value.id}/flush`, {
                method: "DELETE",
            });

            await refreshNuxtData(NuxtKeys.Projects.Search);
            await navigateTo($localeRoute({ name: "projects" }));
        } catch (error) {
            console.warn(error);

            if (error instanceof FetchError) {
                const parsedError = ApiErrorSchema.safeParse(error.data);
                if (!parsedError.success) {
                    errorToast.handle(ResponseCodesRecord.Server.UnknownError);
                    return;
                }

                errorToast.handle(parsedError.data.error);
            }
        }
    }
</script>

<template>
    <AlertDialogContent>
        <AlertDialogHeader>
            <AlertDialogTitle>
                {{ $t("projects.id.sections.settings.delete.modal.title") }}
            </AlertDialogTitle>
            <AlertDialogDescription as-child>
                <div class="flex flex-col space-y-3">
                    <i18n-t
                        keypath="projects.id.sections.settings.delete.modal.description"
                        tag="p"
                    >
                        <template #project>
                            <strong>{{ project?.name }}</strong>
                        </template>
                    </i18n-t>

                    <i18n-t
                        keypath="projects.id.sections.settings.delete.modal.type_project"
                        tag="p"
                    >
                        <template #validation>
                            <code class="rounded bg-muted px-1 py-0.5 font-mono font-bold text-xs">
                                {{ expectedConfirmation }}
                            </code>
                        </template>
                    </i18n-t>
                </div>
            </AlertDialogDescription>

            <div class="pt-2">
                <Input
                    v-model="userInput"
                    :placeholder="expectedConfirmation"
                    autocomplete="off"
                    class="font-mono text-sm"
                />
            </div>

            <AlertDialogFooter>
                <AlertDialogAction
                    :disabled="!isValid"
                    class="bg-destructive text-white hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                    @click="handleDelete"
                >
                    {{ $t("projects.id.sections.settings.delete.label") }}
                </AlertDialogAction>
                <AlertDialogCancel> {{ $t("common.actions.cancel") }} </AlertDialogCancel>
            </AlertDialogFooter>
        </AlertDialogHeader>
    </AlertDialogContent>
</template>
