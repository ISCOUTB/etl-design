<script setup lang="ts">
    const { tables } = useProject();

    const route = useRoute();

    const model = useState<string>(NuxtKeys.Projects.Tables.View(route.path), () => "");
    const events = useAppEvents();

    const animations = useViewManagerAnimations();
    const views = useViewManager(
        () => [
            {
                meta: {
                    label: "",
                    value: "list",
                },
                component: () => import("~/components/project/tables/ProjectTablesList.vue"),
                props: {},
            },
            {
                meta: {
                    label: "",
                    value: "details",
                },
                component: () =>
                    import("~/components/project/tables/details/ProjectTablesDetails.vue"),
                props: {},
            },
        ],
        { model, key: NuxtKeys.Projects.Tables.TabsManager(route.path) },
    );

    onMounted(() => {
        events.on("event:projects:table:change-view", async ({ value }) => {
            await nextTick();
            views.dispatch.setActive(value);
        });
    });
</script>

<template>
    <div class="flex flex-col w-full grow gap-8">
        <div class="flex flex-col gap-4">
            <div class="space-y-0.5">
                <h2 class="text-lg font-medium text-foreground">
                    {{ $t("projects.id.sections.tables.header.title") }}
                </h2>
                <p class="text-sm text-muted-foreground">
                    {{
                        $t("projects.id.sections.tables.header.description", {
                            length: tables.state.value.tableSchemas.length,
                        })
                    }}
                </p>
            </div>
        </div>

        <Transition
            mode="out-in"
            :css="false"
            @enter="animations.onPanelEnter"
            @leave="animations.onPanelLeave"
        >
            <component
                :is="views.computed.component.value"
                v-if="views.computed.component.value"
                v-bind="{ ...views.computed.props.value }"
            />
        </Transition>
    </div>
</template>
