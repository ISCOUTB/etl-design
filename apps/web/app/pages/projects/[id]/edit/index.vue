<script setup lang="ts">
    import type { z } from "zod";

    definePageMeta({
        title: "projects.edit.title",
        layout: "sidebar",
        middleware: ["sidebase-auth", "project-validation"],
        i18n: {
            paths: {
                en: "/projects/[id]/edit",
            },
        },
    });

    const { locale } = useI18n();

    useSeoMeta({
        ogType: "website",
        ogTitle: () => $t("projects.edit.title"),
        ogLocale: () => locale.value.replace("-", "_"),
        robots: "noindex, nofollow",
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
