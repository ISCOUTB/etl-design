<script setup lang="ts">
    import { ResponseCodesRecord } from "#shared/utils/response-codes";
    import { ApiErrorSchema, ResponseProjectSchema } from "#shared/utils/schemas/api";

    definePageMeta({
        title: "projects.id.fallback_title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects/[id]",
            },
        },
    });

    const projectId = useRouteParams("id");
    const setI18nParams = useSetI18nParams();
    setI18nParams({ en: { id: projectId.value } });

    const auth = useAuth();
    useHead({
        title: $t("projects.id.title", {
            username: auth.data.value?.user.name,
        }),
    });

    const errorToast = useServerErrorToast();
    const tabs = useProjectTabs();
    const { data: _data } = useApiFetch(`/projects/id/${projectId.value}`, {
        method: "GET",
        onResponseError({ response }) {
            console.warn(response);
            console.warn(response._data);

            const parsedError = ApiErrorSchema.safeParse(response._data);
            if (!parsedError.success) {
                errorToast.handle(ResponseCodesRecord.Server.UnknownError);
                return;
            }

            errorToast.handle(parsedError.data.error);
        },
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
    <div class="mx-auto w-full max-w-5xl">
        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground text-balance">
                project.Name
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">project.description</p>
        </div>

        <pre>
            {{ data }}
        </pre>

        <Tabs default-value="section:general-information">
            <TabsList>
                <TabsTrigger
                    v-for="tab in tabs.tabs.value"
                    :key="tab.meta.value"
                    :value="tab.meta.value"
                    @click="tabs.setActiveTab(tab.meta.value)"
                >
                    <component :is="tab.meta.icon" v-if="tab.meta.icon" class="size-4" />
                    <span>{{ $t(tab.meta.label) }}</span>
                </TabsTrigger>
            </TabsList>
            <TabsContent :value="tabs.activeTabValue.value!">
                <component
                    :is="tabs.component.value"
                    v-if="tabs.component.value"
                    v-bind="tabs.props.value"
                />
            </TabsContent>
        </Tabs>
    </div>
</template>
