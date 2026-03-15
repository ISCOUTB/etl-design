<script setup lang="ts">
    import type { z } from "zod";

    definePageMeta({
        title: "projects.edit.title",
        layout: "sidebar",
        middleware: ["project-validation"],
        i18n: {
            paths: {
                en: "/projects/[id]/edit",
            },
        },
    });

    useSeoMeta({
        ogType: "website",
    });

    const projectId = useRouteParams("id");
    const setI18nParams = useSetI18nParams();
    setI18nParams({ en: { id: projectId.value } });

    const KEY = NuxtKeys.Projects.SharedState(projectId.value?.toString());
    const sharedState = useState<z.infer<typeof ResponseProjectSchema>>(KEY);
</script>

<template>
    <div>
        <ProjectUpdateForm :project="sharedState" class="mx-auto w-full max-w-2xl" />
        <div class="my-6" />
    </div>
</template>
