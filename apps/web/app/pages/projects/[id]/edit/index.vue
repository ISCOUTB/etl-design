<script setup lang="ts">
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

    const projectId = useRouteParams("id");
    const setI18nParams = useSetI18nParams();
    setI18nParams({ en: { id: projectId.value } });

    const errorToast = useErrorToast();
    const { data: _data, status } = await useApiFetch(`/projects/id/${projectId.value}`, {
        method: "GET",
        onResponseError({ response }) {
            const parsedError = ApiErrorSchema.safeParse(response._data);
            if (!parsedError.success) {
                errorToast.handle(ResponseCodesRecord.Server.UnknownError);
                return;
            }

            errorToast.handle(parsedError.data.error);
        },
        key: NuxtKeys.Projects.Id,
        cache: "no-cache",
    });
    const data = computed(() => {
        if (status.value === "pending" || !_data.value) {
            return;
        }

        const parsed = ResponseProjectSchema.safeParse(_data.value);
        if (!parsed.success) {
            errorToast.handle(ResponseCodesRecord.Server.BadPayload);
            return;
        }

        return parsed.data;
    });
</script>

<template>
    <ProjectUpdateForm :project="data" class="mx-auto w-full max-w-2xl" />
</template>
