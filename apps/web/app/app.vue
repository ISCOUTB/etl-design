<script setup lang="ts">
    import "vue-sonner/style.css";

    const { finalizePendingLocaleChange } = useI18n();

    async function onBeforeEnter() {
        await finalizePendingLocaleChange();
    }
</script>

<template>
    <div>
        <NuxtLayout>
            <NuxtLoadingIndicator />
            <NuxtPage :transition="{ name: 'my', mode: 'in-out', onBeforeEnter }" />
            <Toaster />
        </NuxtLayout>
    </div>
</template>

<style>
    .my-enter-active,
    .my-leave-active {
        transition: opacity 0.3s;
    }
    .my-enter,
    .my-leave-active {
        opacity: 0;
    }
</style>
