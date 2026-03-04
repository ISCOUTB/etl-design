<script setup lang="ts">
    definePageMeta({
        title: "projects.create.header.title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects/create",
            },
        },
    });
</script>

<template>
    <ProjectCreateForm class="mx-auto w-full max-w-2xl" />
</template>
