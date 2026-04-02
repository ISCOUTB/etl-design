<script setup lang="ts">
    import { FileIcon, Info, Settings, Table, Upload } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

    definePageMeta({
        title: "projects.id.fallback_title",
        layout: "sidebar",
        middleware: ["sidebase-auth", "project-validation"],
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
    const { state, uploadSchema } = useProvideProjectState(projectId.value?.toString());

    const auth = useAuth();
    useHead({
        title: $t("projects.id.title", {
            username: auth.data.value?.user.name,
            projectName: state.project.value?.name,
        }),
    });

    const animations = useViewManagerAnimations();
    const views = useViewManager(
        () => [
            {
                meta: {
                    label: "projects.id.sections.overview.tab",
                    value: state.VIEWS.value.Overview,
                    icon: Info,
                },
                component: () => import("~/components/project/overview/ProjectOverview.vue"),
                props: {},
            },
            {
                meta: {
                    label: "projects.id.sections.upload_schema.tab",
                    value: state.VIEWS.value.UploadFile,
                    icon: Upload,
                },
                component: () =>
                    import("@/components/project/upload-schema/ProjectUploadSchema.vue"),
                props: {},
            },
            {
                meta: {
                    label: "projects.id.sections.tables.tab",
                    value: state.VIEWS.value.Tables,
                    icon: Table,
                },
                component: () => import("~/components/project/tables/ProjectTables.vue"),
                props: {},
            },
            {
                meta: {
                    label: "projects.id.sections.settings.tab",
                    value: state.VIEWS.value.Settings,
                    icon: Settings,
                },
                component: () => import("@/components/project/ProjectSettings.vue"),
                props: {},
            },
        ],
        { model: state.view },
    );

    watch(
        () => uploadSchema.state.value.uploadedFile,
        (file) => {
            const hasTab = views.computed.filteredViews.value.some(
                (entry) => entry.meta.value === state.VIEWS.value.File,
            );

            if (file && !hasTab) {
                views.dispatch.addView({
                    meta: {
                        label: "projects.id.sections.file.tab",
                        value: state.VIEWS.value.File,
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
                views.dispatch.removeView(state.VIEWS.value.File);
            }
        },
        { immediate: true },
    );

    const events = useAppEvents();
    onMounted(() => {
        views.dispatch.preload([state.VIEWS.value.UploadFile, state.VIEWS.value.Settings]);
        events.on("event:projects:change-tab", ({ value }) => views.dispatch.setActive(value));
    });
</script>

<template>
    <div class="mx-auto w-full max-w-5xl">
        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground text-balance">
                {{ state.project.value.name }}
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">
                {{ state.project.value.description }}
            </p>
        </div>

        <Tabs v-model="state.view.value" :default-value="state.VIEWS.value.Overview">
            <TabsList>
                <TabsTrigger
                    v-for="entry in views.computed.filteredViews.value"
                    :key="entry.meta.value"
                    :value="entry.meta.value"
                    :class="entry.meta.class"
                    @click="views.dispatch.setActive(entry.meta.value)"
                >
                    <component :is="entry.meta.icon" v-if="entry.meta.icon" />
                    <span>
                        {{ $t(entry.meta.label) }}
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
                    v-if="views.state.activeView.value && views.computed.component.value"
                    :key="views.state.activeView.value"
                    :value="views.state.activeView.value"
                    class="mt-6"
                >
                    <component
                        :is="views.computed.component.value"
                        v-bind="{ ...views.computed.props.value }"
                    />
                </TabsContent>
            </Transition>
        </Tabs>

        <div class="my-24" />
    </div>
</template>
