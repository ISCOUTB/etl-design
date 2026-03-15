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

    useSeoMeta({
        title: $t("projects.create.header.title"),
        description: $t("projects.create.header.description"),
    });
</script>

<template>
    <div>
        <ProjectCreateForm class="mx-auto w-full max-w-5xl" />
        <div class="my-6" />
    </div>
</template>
