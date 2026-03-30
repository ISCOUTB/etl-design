<script setup lang="ts">
    import { FileIcon, Info, Settings, Table, Upload } from "lucide-vue-next";
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

    const { locale } = useI18n();

    useSeoMeta({
        ogType: "website",
        ogTitle: () => $t("projects.id.fallback_title"),
        ogLocale: () => locale.value.replace("-", "_"),
        robots: "index, follow",
    });

    const projectId = useRouteParams("id");
    const setI18nParams = useSetI18nParams();
    setI18nParams({ en: { id: projectId.value } });

    const { Section, tab, schema, project } = useProjectTabsSharedState();

    const auth = useAuth();
    useHead({
        title: $t("projects.id.title", {
            username: auth.data.value?.user.name,
            projectName: project.value?.name,
        }),
    });

    const animations = useTabsAnimations();

    const tabs = useTabsManager(
        () => [
            {
                tab: {
                    label: "projects.id.sections.overview.tab",
                    value: Section.value.Overview,
                    icon: Info,
                },
                component: () => import("~/components/project/overview/ProjectOverview.vue"),
                props: {},
            },
            {
                tab: {
                    label: "projects.id.sections.upload_schema.tab",
                    value: Section.value.UploadFile,
                    icon: Upload,
                },
                component: () =>
                    import("@/components/project/upload-schema/ProjectUploadSchema.vue"),
                props: {
                    project,
                },
            },
            {
                tab: {
                    label: "projects.id.sections.tables.tab",
                    value: Section.value.Tables,
                    icon: Table,
                },
                component: () => import("~/components/project/tables/ProjectTables.vue"),
                props: {
                    project,
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
                    project,
                },
            },
        ],
        { model: tab },
    );

    watch(
        () => schema.state.value.uploadedFile,
        (file) => {
            const hasTab = tabs.filteredTabs.value.some(
                (entry) => entry.tab.value === Section.value.File,
            );

            if (file && !hasTab) {
                tabs.dispatch.addTab({
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
                tabs.dispatch.removeTab(Section.value.File);
            }
        },
        { immediate: true },
    );

    const events = useAppEvents();

    onMounted(() => {
        tabs.dispatch.preload([Section.value.UploadFile, Section.value.Settings]);

        events.on("event:projects:change-tab", ({ value }) => tabs.dispatch.setActive(value));
    });
</script>

<template>
    <div class="mx-auto w-full max-w-5xl">
        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground text-balance">
                {{ project.name }}
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">{{ project.description }}</p>
        </div>

        <Tabs v-model="tab" :default-value="Section.Overview">
            <TabsList>
                <TabsTrigger
                    v-for="entry in tabs.filteredTabs.value"
                    :key="entry.tab.value"
                    :value="entry.tab.value"
                    :class="entry.tab.class"
                    @click="tabs.dispatch.setActive(entry.tab.value)"
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

        <div class="my-24" />
    </div>
</template>
