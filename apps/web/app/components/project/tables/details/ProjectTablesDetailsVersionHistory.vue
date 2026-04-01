<script setup lang="ts">
    import { ChevronsRight, History, RotateCcw } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    const {
        state: { project },
        tables,
    } = useProject();

    const sortedSchemaReleases = computed(() => {
        if (!tables.state.value.selectedSchema) {
            return;
        }

        return tables.state.value.selectedSchema.schemas_releases.toSorted(
            (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
    });

    const animations = useCollapsibleAnimations();

    const modal = useModal();
    function handleRevert(_event: Event) {
        if (!project.value) {
            return;
        }

        modal.dispatch.loadComponent({
            loader: () => import("~/components/project/tables/ProjectTablesDeleteModal.vue"),
            key: ModalKeys.Projects.Tables.Delete,
            props: {
                table: tables.state.value.selectedSchema,
                projectId: project.value.id,
                kind: "revert",
                onSuccess: () => {
                    const updated = tables.state.value.tableSchemas.find(
                        (_schema) => _schema.id === tables.state.value.selectedSchema?.id,
                    );

                    if (updated) {
                        tables.dispatch.setSelectedSchema(updated);
                    }
                },
            },
        });
    }
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <History class="size-4 text-muted-foreground" />
                    <span class="text-sm font-medium text-foreground">
                        {{ $t("projects.id.sections.tables.details.version_history.title") }}
                    </span>
                </div>
                <div>
                    <Badge variant="secondary" class="text-xs font-normal">
                        {{
                            $t("projects.id.sections.tables.details.version_history.releases", {
                                count: tables.state.value.selectedSchema?.schemas_releases.length,
                            })
                        }}
                    </Badge>
                </div>
            </CardTitle>
        </CardHeader>
        <CardContent v-if="sortedSchemaReleases">
            <template v-if="sortedSchemaReleases.length > 0">
                <div class="divide-y">
                    <template
                        v-for="(release, index) in sortedSchemaReleases"
                        :key="release.created_at"
                    >
                        <Collapsible v-slot="{ open }">
                            <CollapsibleTrigger as-child class="w-full cursor-pointer">
                                <Item class="w-full bg-muted/30 py-3.5">
                                    <ItemMedia>
                                        <Avatar>
                                            <AvatarFallback>
                                                {{ `v${sortedSchemaReleases.length - index}` }}
                                            </AvatarFallback>
                                        </Avatar>
                                    </ItemMedia>
                                    <ItemContent>
                                        <ItemTitle class="flex-col gap-0.5 items-start">
                                            <div>
                                                {{
                                                    new Date(release.created_at).toLocaleDateString(
                                                        $i18n.locale,
                                                        {
                                                            month: "short",
                                                            day: "numeric",
                                                            year: "numeric",
                                                            hour: "2-digit",
                                                            minute: "2-digit",
                                                            timeZone: "UTC",
                                                        },
                                                    )
                                                }}
                                            </div>

                                            <div class="text-left text-muted-foreground text-xs">
                                                {{
                                                    $t(
                                                        "projects.id.sections.tables.details.overview.columns",
                                                        {
                                                            count: Object.entries(
                                                                release.schema.properties,
                                                            ).length,
                                                        },
                                                    )
                                                }}
                                            </div>
                                        </ItemTitle>
                                    </ItemContent>
                                    <ItemActions>
                                        <div class="flex items-center space-x-2">
                                            <Button
                                                v-if="index === 0"
                                                size="sm"
                                                variant="outline"
                                                class="pointer-events-auto"
                                                @click.stop="handleRevert"
                                            >
                                                <RotateCcw class="size-4" />
                                                {{
                                                    $t(
                                                        "projects.id.sections.tables.details.version_history.revert",
                                                    )
                                                }}
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                :class="cn(open && 'rotate-90 border-transparent')"
                                            >
                                                <ChevronsRight class="size-5" />
                                            </Button>
                                        </div>
                                    </ItemActions>
                                </Item>
                            </CollapsibleTrigger>
                            <Transition
                                :css="false"
                                @enter="animations.onEnter"
                                @leave="animations.onLeave"
                            >
                                <CollapsibleContent v-if="open" force-mount class="mt-4">
                                    <div class="space-y-4">
                                        <ProjectTablesDetailsPropertiesTable
                                            :properties="Object.entries(release.schema.properties)"
                                        />

                                        <CodeBlock :content="release.schema" />
                                    </div>
                                </CollapsibleContent>
                            </Transition>
                        </Collapsible>
                    </template>
                </div>
            </template>
            <template v-else>
                <Empty>
                    <EmptyHeader>
                        <EmptyMedia variant="icon">
                            <History />
                        </EmptyMedia>
                        <EmptyTitle>
                            {{
                                $t(
                                    "projects.id.sections.tables.details.version_history.no_versions.title",
                                )
                            }}
                        </EmptyTitle>
                        <EmptyDescription>
                            {{
                                $t(
                                    "projects.id.sections.tables.details.version_history.no_versions.description",
                                )
                            }}
                        </EmptyDescription>
                    </EmptyHeader>
                </Empty>
            </template>
        </CardContent>
    </Card>
</template>
