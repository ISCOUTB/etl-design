<script setup lang="ts">
    import { RotateCcw, Trash2 } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    interface Props {
        table: MaybeRefOrGetter<MongoRaw | undefined>;
        projectId: ResponseProject["id"];
        kind: "revert" | "delete";
        onSuccess?: () => void | (() => Promise<void>);
    }

    const props = defineProps<Props>();
    const table = computed(() => toValue(props.table));
    const actions = useProjectTableActions();
    const errorToast = useErrorToast();

    const expectedConfirmation = computed(() => {
        if (!table.value) {
            return;
        }

        const currentTable = TableUtils.getTableName(table.value.import_name);
        const currentKind = props.kind;

        if (currentKind === "delete") {
            return $t("projects.id.sections.tables.delete.validation.delete", {
                value: currentTable,
            });
        }

        return $t("projects.id.sections.tables.delete.validation.revert", {
            value: currentTable,
        });
    });

    const userInput = ref<string>("");
    const isValid = computed(() => userInput.value === expectedConfirmation.value);

    function handleDelete(_event: Event) {
        if (!table.value) {
            return;
        }

        actions
            .handleSchemaTransition(props.projectId, table.value?.import_name)
            .then(async () => {
                await refreshNuxtData(NuxtKeys.Projects.Tables.RawSchemas(props.projectId));

                if (props.kind === "delete") {
                    toast.success($t("projects.id.sections.tables.events.table_deleted.title"), {
                        description: $t(
                            "projects.id.sections.tables.events.table_deleted.description",
                        ),
                    });
                }

                if (props.kind === "revert") {
                    toast.success($t("projects.id.sections.tables.events.table_reverted.title"), {
                        description: $t(
                            "projects.id.sections.tables.events.table_reverted.description",
                        ),
                    });
                }

                handleCloseModal();

                if (props.onSuccess) {
                    await props.onSuccess();
                }
            })
            .catch((error) => errorToast.handleServer(error));
    }

    const modal = useModal();
    function handleCloseModal() {
        if (modal.state.value.currentModalKey === ModalKeys.Projects.Tables.Delete) {
            modal.dispatch.setOpen(false);
        }
    }

    const { define: DefineDescription, reuse: ReuseDescription } = createReusableTemplate();
    const { define: DefineInput, reuse: ReuseInput } = createReusableTemplate();
    const { define: DefineLoader, reuse: ReuseLoader } = createReusableTemplate<{
        icon: Component;
    }>();
</script>

<template>
    <DefineDescription>
        <div class="flex flex-col space-y-3">
            <template v-if="kind === 'delete'">
                <i18n-t
                    v-if="table"
                    keypath="projects.id.sections.tables.delete.modal.description.delete"
                    tag="p"
                >
                    <template #table>
                        <strong>{{ TableUtils.getTableName(table.import_name) }}</strong>
                    </template>
                </i18n-t>
            </template>
            <template v-if="kind === 'revert'">
                {{ $t("projects.id.sections.tables.delete.modal.description.revert") }}
            </template>
            <i18n-t keypath="projects.id.sections.tables.delete.modal.type_table" tag="p">
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
            :spellcheck="false"
            class="font-mono text-sm"
        />
    </DefineInput>

    <DefineLoader v-slot="{ icon }">
        <UtilsLoading :loading="actions.state.loading">
            <template #default>
                <component :is="icon" />
            </template>
        </UtilsLoading>
    </DefineLoader>

    <ResponsiveModal desktop="alert-dialog" mobile="drawer">
        <template #alert-dialog>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>
                        {{ $t("projects.id.sections.tables.delete.modal.title") }}
                    </AlertDialogTitle>
                    <AlertDialogDescription as-child>
                        <ReuseDescription />
                    </AlertDialogDescription>
                    <div class="pt-2">
                        <ReuseInput />
                    </div>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <template v-if="kind === 'delete'">
                        <AlertDialogAction
                            :disabled="!isValid || actions.state.loading.value"
                            @click="handleDelete"
                        >
                            <ReuseLoader :icon="Trash2" />
                            {{ $t("projects.id.sections.tables.card.dropdown.delete") }}
                        </AlertDialogAction>
                    </template>
                    <template v-if="kind === 'revert'">
                        <AlertDialogAction
                            :disabled="!isValid || actions.state.loading.value"
                            @click="handleDelete"
                        >
                            <ReuseLoader :icon="RotateCcw" />
                            {{ $t("projects.id.sections.tables.card.dropdown.revert") }}
                        </AlertDialogAction>
                    </template>

                    <AlertDialogCancel @click="handleCloseModal">
                        {{ $t("common.actions.cancel") }}
                    </AlertDialogCancel>
                </AlertDialogFooter>
            </AlertDialogContent>
        </template>
        <template #drawer>
            <DrawerContent>
                <DrawerHeader>
                    <DrawerTitle>
                        {{ $t("projects.id.sections.tables.delete.modal.title") }}
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
                        <template v-if="kind === 'delete'">
                            <Button
                                :disabled="!isValid || actions.state.loading.value"
                                class="bg-destructive text-white hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                                @click="handleDelete"
                            >
                                <ReuseLoader :icon="Trash2" />
                                {{ $t("projects.id.sections.tables.card.dropdown.delete") }}
                            </Button>
                        </template>
                        <template v-if="kind === 'revert'">
                            <Button
                                variant="outline"
                                :disabled="!isValid || actions.state.loading.value"
                                @click="handleDelete"
                            >
                                <ReuseLoader :icon="RotateCcw" />
                                {{ $t("projects.id.sections.tables.card.dropdown.revert") }}
                            </Button>
                        </template>
                        <Button @click="handleCloseModal">
                            {{ $t("common.actions.cancel") }}
                        </Button>
                    </div>
                </DrawerFooter>
            </DrawerContent>
        </template>
    </ResponsiveModal>
</template>
