<script setup lang="ts">
    import { ResponseCodesRecord } from "#shared/utils/response-codes";
    import { ApiErrorSchema, ResponseProjectSchema } from "#shared/utils/schemas/api";
    import { Info, Settings } from "lucide-vue-next";

    definePageMeta({
        title: "projects.id.fallback_title",
        layout: "sidebar",
        middleware: ["project-validation"],
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

    const Section = computed(() => ({
        General: $t("projects.id.sections.general_information.tab"),
        Settings: $t("projects.id.sections.settings.tab"),
    }));

    const tab = useRouteQuery("tab", Section.value.General, { mode: "replace" });

    const errorToast = useErrorToast();
    const { data: _data } = useApiFetch(`/projects/id/${projectId.value}`, {
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
    <div class="mx-auto w-full max-w-5xl">
        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground text-balance">
                {{ data?.name }}
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">{{ data?.description }}</p>
        </div>

        <Tabs v-model="tab" :default-value="Section.General">
            <TabsList>
                <TabsTrigger :value="Section.General" class="flex items-center">
                    <Info />
                    <span>
                        {{ $t("projects.id.sections.general_information.tab") }}
                    </span>
                </TabsTrigger>
                <TabsTrigger :value="Section.Settings" class="flex items-center">
                    <Settings />
                    <span>
                        {{ $t("projects.id.sections.settings.tab") }}
                    </span>
                </TabsTrigger>
            </TabsList>
            <TabsContent :value="Section.General" class="mt-6">
                <LazyProjectGeneralInformation :project="data" hydrate-on-visible />
            </TabsContent>
            <TabsContent :value="Section.Settings" class="mt-6">
                <LazyProjectSettings :project="data" hydrate-on-visible />
            </TabsContent>
        </Tabs>
    </div>
</template>
