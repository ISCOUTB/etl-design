<script setup lang="ts">
    interface Props {
        table: MaybeRefOrGetter<MongoRaw | undefined>;
    }

    const props = defineProps<Props>();
    const table = computed(() => toValue(props.table));

    const expectedConfirmation = computed(() => {
        if (!table.value) {
            return;
        }
        return $t("projects.id.sections.tables.delete.validation", {
            value: TableUtils.getTableName(table.value.import_name),
        });
    });

    const userInput = useState(NuxtKeys.Projects.Tables.Delete.Validation(table.value), () => "");
    const isValid = computed(() => userInput.value === expectedConfirmation.value);

    function handleDelete() {}

    const modal = useModal();
    function handleCancel() {
        if (modal.state.value.currentModalKey === ModalKeys.Projects.Tables.Delete) {
            modal.dispatch.setOpen(false);
        }
    }

    const { define: DefineDescription, reuse: ReuseDescription } = createReusableTemplate();
    const { define: DefineInput, reuse: ReuseInput } = createReusableTemplate();
</script>

<template>
    <DefineDescription>
        <div class="flex flex-col space-y-3">
            <i18n-t
                v-if="table"
                keypath="projects.id.sections.tables.delete.modal.description"
                tag="p"
            >
                <template #table>
                    <strong>{{ TableUtils.getTableName(table.import_name) }}</strong>
                </template>
            </i18n-t>
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
            class="font-mono text-sm"
        />
    </DefineInput>

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
                    <AlertDialogAction
                        :disabled="!isValid"
                        class="bg-destructive text-white hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                        @click="handleDelete"
                    >
                        {{ $t("projects.id.sections.settings.delete.label") }}
                    </AlertDialogAction>
                    <AlertDialogCancel @click="handleCancel">
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
                        <Button
                            :disabled="!isValid"
                            class="bg-destructive text-white hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                            @click="handleDelete"
                        >
                            {{ $t("projects.id.sections.settings.delete.label") }}
                        </Button>
                        <Button @click="handleCancel">
                            {{ $t("common.actions.cancel") }}
                        </Button>
                    </div>
                </DrawerFooter>
            </DrawerContent>
        </template>
    </ResponsiveModal>
</template>
