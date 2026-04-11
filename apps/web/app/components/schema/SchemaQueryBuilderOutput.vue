<script setup lang="ts">
    const qb = useQueryBuilder();

    const {
        state: { project },
    } = useProject();

    const view = useState(
        NuxtKeys.Projects.QueryBuilder.SelectedOutput(
            project.value.id,
            qb.state.activeSchema.value.import_name,
        ),
        () => "sql",
    );
    const views = useViewManager(
        [
            {
                meta: {
                    label: "projects.id.sections.query_builder.output.sql",
                    value: "sql",
                },
                component: () => import("@/components/common/code-block/CodeBlock.vue"),
                props: {
                    content: qb.computed.generatedSQL,
                },
            },
            {
                meta: {
                    label: "projects.id.sections.query_builder.output.native",
                    value: "native",
                },
                component: () => import("@/components/common/code-block/CodeBlock.vue"),
                props: {
                    content: qb.computed.queryOutput,
                    ext: "json",
                },
            },
            {
                meta: {
                    label: "projects.id.sections.query_builder.output.tree",
                    value: "tree",
                },
                component: () => import("@/components/common/code-block/CodeBlock.vue"),
                props: {
                    content: qb.computed.queryTree,
                    ext: "json",
                },
            },
        ],
        { key: "query-builder", model: view },
    );
    const animations = useViewManagerAnimations();

    onMounted(() => {
        views.dispatch.preload();
    });
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle>{{ $t("projects.id.sections.query_builder.cards.output.title") }}</CardTitle>
            <CardDescription>
                {{ $t("projects.id.sections.query_builder.cards.output.description") }}
            </CardDescription>
        </CardHeader>
        <CardContent>
            <Tabs v-model="view" default-value="sql">
                <TabsList class="w-full">
                    <TabsTrigger
                        v-for="entry in views.computed.filteredViews.value"
                        :key="entry.meta.value"
                        :value="entry.meta.value"
                        :class="entry.meta.class"
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
                        class="mt-2"
                    >
                        <component
                            :is="views.computed.component.value"
                            v-bind="{ ...views.computed.props.value }"
                        />
                    </TabsContent>
                </Transition>
            </Tabs>
        </CardContent>
    </Card>
</template>
