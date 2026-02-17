<script setup lang="ts">
    const { finalizePendingLocaleChange } = useI18n();

    async function onBeforeEnter() {
        await finalizePendingLocaleChange();
    }
</script>

<template>
    <NuxtLayout>
        <NuxtPage :transition="{ name: 'my', mode: 'in-out', onBeforeEnter }" />
    </NuxtLayout>
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
