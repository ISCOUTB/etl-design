<script setup lang="ts">
    import type { z } from "zod";
    import { Database, FileIcon, Info, Settings } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

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

    const { Section, tab, uploadedFile } = useProjectTabsSharedState();

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
                props: {},
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

    watch(
        uploadedFile,
        (file) => {
            const hasTab = tabs.tabs.value.has(Section.value.File);

            if (file && !hasTab) {
                tabs.addTab({
                    tab: {
                        label: "projects.id.sections.file.tab",
                        value: Section.value.File,
                        icon: FileIcon,
                        class: cn(
                            "relative transition-colors",
                            "data-[state=inactive]:font-semibold data-[state=inactive]:border",
                            "data-[state=active]:ring-2",

                            "data-[state=inactive]:bg-amber-100 data-[state=inactive]:text-amber-900",
                            "data-[state=inactive]:border-amber-300",
                            "data-[state=active]:ring-amber-300/70",

                            "dark:data-[state=inactive]:bg-amber-500/20 dark:data-[state=inactive]:text-amber-100",
                            "dark:data-[state=inactive]:border-amber-400/40",
                            "dark:data-[state=active]:ring-amber-400/40",
                        ),
                    },
                    component: () => import("@/components/project/ProjectFileVisualizer.vue"),
                    props: {},
                });

                return;
            }

            if (!file && hasTab) {
                tabs.removeTab(Section.value.File);
            }
        },
        { immediate: true },
    );

    onMounted(() => {
        tabs.preloadTabs([Section.value.Schema, Section.value.Settings]);
    });
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
                <TabsTrigger
                    v-for="entry in tabs.tabs.value.values()"
                    :key="entry.tab.value"
                    :value="entry.tab.value"
                    :class="entry.tab.class"
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
                    <component :is="tabs.component.value" v-bind="{ ...tabs.props.value }" />
                </TabsContent>
            </Transition>
        </Tabs>
    </div>
</template>
