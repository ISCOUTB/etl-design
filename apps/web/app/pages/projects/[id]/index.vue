<script setup lang="ts">
    import type { z } from "zod";
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

    const KEY = NuxtKeys.Projects.SharedState(projectId.value?.toString());
    const sharedState = useState<z.infer<typeof ResponseProjectSchema>>(KEY);

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
</script>

<template>
    <div class="mx-auto w-full max-w-5xl">
        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground text-balance">
                {{ sharedState.name }}
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">{{ sharedState.description }}</p>
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
                <LazyProjectGeneralInformation :project="sharedState" hydrate-on-visible />
            </TabsContent>
            <TabsContent :value="Section.Settings" class="mt-6">
                <LazyProjectSettings :project="sharedState" hydrate-on-visible />
            </TabsContent>
        </Tabs>
    </div>
</template>
