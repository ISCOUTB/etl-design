<script setup lang="ts">
    interface Props {
        mobile?: Components.Modal.Kind;
        desktop?: Components.Modal.Kind;
    }

    interface Slots {
        sheet?: () => unknown;
        dialog?: () => unknown;
        "alert-dialog"?: () => unknown;
        drawer?: () => unknown;
    }

    const props = withDefaults(defineProps<Props>(), { desktop: "dialog", mobile: "sheet" });

    defineSlots<Slots>();

    const { resolve } = useResponsiveModal();
    const kind = computed(() => resolve(props.desktop, props.mobile));
    const modal = useModal();

    watch(kind, (next) => modal.dispatch.setModalKind(next), { immediate: true });
</script>

<template>
    <div>
        <slot v-if="kind === 'sheet'" name="sheet" />
        <slot v-if="kind === 'dialog'" name="dialog" />
        <slot v-if="kind === 'alert-dialog'" name="alert-dialog" />
        <slot v-if="kind === 'drawer'" name="drawer" />
    </div>
</template>
