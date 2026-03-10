<script setup lang="ts">
    import type { z } from "zod";
    import { Database, Info, Settings } from "lucide-vue-next";

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
            projectName: sharedState.value.name,
        }),
    });

    const Section = computed(() => ({
        General: $t("projects.id.sections.general_information.tab"),
        Schema: $t("projects.id.sections.schema.tab"),
        Settings: $t("projects.id.sections.settings.tab"),
    }));

    const tab = useRouteQuery("tab", Section.value.General, {
        mode: "replace",
        transform: (value) => {
            const sections = Object.values(Section.value);
            const found = sections.find((section) => section === value);
            if (found) {
                return found;
            }

            return Section.value.General;
        },
    });

    const animations = useTabsAnimations();
    const tabs = useTabsManager(
        [
            {
                tab: {
                    label: "projects.id.sections.general_information.tab",
                    value: Section.value.General,
                    icon: Info,
                },
                component: () => import("@/components/project/ProjectGeneralInformation.vue"),
                props: {
                    project: sharedState,
                },
            },
            {
                tab: {
                    label: "projects.id.sections.schema.tab",
                    value: Section.value.Schema,
                    icon: Database,
                },
                component: () => import("@/components/project/ProjectSchema.vue"),
                props: {
                    project: sharedState,
                },
            },
            {
                tab: {
                    label: "projects.id.sections.settings.tab",
                    value: Section.value.Settings,
                    icon: Settings,
                },
                component: () => import("@/components/project/ProjectSettings.vue"),
                props: {
                    project: sharedState,
                },
            },
        ],
        { model: tab },
    );
</script>

<template>
    <div class="mx-auto w-full max-w-5xl">
        <pre>
            {{ auth.data.value?.accessToken }}
        </pre>

        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground text-balance">
                {{ sharedState.name }}
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">{{ sharedState.description }}</p>
        </div>

        <Tabs v-model="tab" :default-value="Section.General">
            <TabsList>
                <TabsTrigger
                    v-for="entry in tabs.tabs.value.values()"
                    :key="entry.tab.value"
                    :value="entry.tab.value"
                    @click="tabs.setActive(entry.tab.value)"
                >
                    <component :is="entry.tab.icon" v-if="entry.tab.icon" />
                    <span>
                        {{ $t(entry.tab.label) }}
                    </span>
                </TabsTrigger>
            </TabsList>
            <Transition
                mode="out-in"
                :css="false"
                @enter="animations.onPanelEnter"
                @leave="animations.onPanelLeave"
            >
                <TabsContent
                    v-if="tabs.activeTab.value && tabs.component.value"
                    :key="tabs.activeTab.value"
                    :value="tabs.activeTab.value"
                    class="mt-6"
                >
                    <component :is="tabs.component.value" v-bind="tabs.props.value" />
                </TabsContent>
            </Transition>
        </Tabs>
    </div>
</template>
