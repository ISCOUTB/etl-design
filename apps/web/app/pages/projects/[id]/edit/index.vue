<script setup lang="ts">
    // TODO
    /**
     * await blocks client-side navigation
     * so, the idea to show a proper skeleton while
     * the information is being fetched hmmmmm
     *
     *
     * I'm sure is completely posible, just gotta figure
     * out how to do it.
     *
     */

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
    const { data: _data } = await useApiFetch(`/projects/id/${projectId.value}`, {
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
    });
    const data = computed(() => {
        const parsed = ResponseProjectSchema.safeParse(_data.value);
        if (!parsed.success) {
            errorToast.handle(ResponseCodesRecord.Server.BadPayload);
            return;
        }

        return parsed.data;
    });
</script>

<template>
    <Suspense>
        <ProjectUpdateForm :project="data" />

        <template #fallback>
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Officiis vitae, illum non
            voluptates veniam minus nam obcaecati fugit quos aliquam! Commodi quasi blanditiis, at
            officiis soluta repellendus dolorem totam iusto!
        </template>
    </Suspense>
</template>
