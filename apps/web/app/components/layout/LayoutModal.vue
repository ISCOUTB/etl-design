<script setup lang="ts">
    const modal = useModal();
    const canRender = computed(() => modal.currentComponent.value && modal.state.value.open);
</script>

<template>
    <div>
        <Sheet
            v-if="modal.state.value.currentKind === 'sheet' && canRender"
            v-model:open="modal.state.value.open"
            v-bind="modal.state.value.containerProps"
        >
            <component
                :is="modal.currentComponent.value"
                v-if="modal.currentComponent.value"
                v-bind="modal.state.value.componentProps"
            />
        </Sheet>

        <Dialog
            v-if="modal.state.value.currentKind === 'dialog' && canRender"
            v-model:open="modal.state.value.open"
            v-bind="modal.state.value.containerProps"
        >
            <component
                :is="modal.currentComponent.value"
                v-if="modal.currentComponent.value"
                v-bind="modal.state.value.componentProps"
            />
        </Dialog>

        <AlertDialog
            v-if="modal.state.value.currentKind === 'alert-dialog' && canRender"
            v-model:open="modal.state.value.open"
            v-bind="modal.state.value.containerProps"
        >
            <component
                :is="modal.currentComponent.value"
                v-if="modal.currentComponent.value"
                v-bind="modal.state.value.componentProps"
            />
        </AlertDialog>

        <Drawer
            v-if="modal.state.value.currentKind === 'drawer' && canRender"
            v-model:open="modal.state.value.open"
            v-bind="modal.state.value.containerProps"
        >
            <component
                :is="modal.currentComponent.value"
                v-if="modal.currentComponent.value"
                v-bind="modal.state.value.componentProps"
            />
        </Drawer>
    </div>
</template>
