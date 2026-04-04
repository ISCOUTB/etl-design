<script setup lang="ts">
    definePageMeta({
        title: "projects.edit.title",
        layout: "sidebar",
        middleware: ["sidebase-auth", "project-validation"],
        i18n: {
            paths: {
                en: "/projects/[id]/edit",
            },
        },
        breadcrumb: {
            options: {
                parent: {
                    kind: "link",
                    overrides: {
                        label: {
                            keypath: "PROJECT_TITLE",
                        },
                    },
                },
            },
        },
    });

    const { locale } = useI18n();
    const { BREADCRUMB_OVERRIDES } = useGlobalState();
    const projectId = useRouteParams("id");
    const setI18nParams = useSetI18nParams();
    setI18nParams({ en: { id: projectId.value } });
    const { state } = useProvideProjectState(projectId.value?.toString());
    useSeoMeta({
        ogType: "website",
        ogTitle: () => $t("projects.edit.title"),
        ogLocale: () => locale.value.replace("-", "_"),
        robots: "noindex, nofollow",
    });
    watchEffect(() => {
        BREADCRUMB_OVERRIDES.value.PROJECT_TITLE = state.project.value.name;
    });
</script>

<template>
    <div>
        <ProjectUpdateForm :project="state.project" class="mx-auto w-full max-w-2xl" />
        <div class="my-6" />
    </div>
</template>
