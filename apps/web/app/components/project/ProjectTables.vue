<script setup lang="ts">
    import { Search } from "lucide-vue-next";

    const { tables } = useProjectTabsSharedState();
    const animations = useTabsAnimations();
    const route = useRoute();

    const model = useState<string>(NuxtKeys.Projects.Tables.View(route.path), () => "");
    const events = useAppEvents();

    const tabs = useTabsManager(
        () => [
            {
                tab: {
                    label: "",
                    value: "overview",
                },
                component: () => import("@/components/project/tables/ProjectTablesOverview.vue"),
                props: {},
            },
            {
                tab: {
                    label: "",
                    value: "view",
                },
                component: () => import("@/components/project/ProjectTableSchemaView.vue"),
                props: {
                    schema: tables.state.value.selectedSchema,
                },
            },
        ],
        { model, key: NuxtKeys.Projects.Tables.TabsManager(route.path) },
    );

    onMounted(() => {
        events.on("event:projects:table:change-view", ({ value }) => {
            tabs.dispatch.setActive(value);
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
            <div>
                <InputGroup class="max-w-md">
                    <InputGroupInput placeholder="Search Tables..." />
                    <InputGroupAddon align="inline-start">
                        <Search class="size-4 text-muted-foreground" />
                    </InputGroupAddon>
                </InputGroup>
            </div>
        </div>

        <Transition
            mode="out-in"
            :css="false"
            @enter="animations.onPanelEnter"
            @leave="animations.onPanelLeave"
        >
            <component :is="tabs.component.value" v-bind="{ ...tabs.props.value }" />
        </Transition>
    </div>
</template>
