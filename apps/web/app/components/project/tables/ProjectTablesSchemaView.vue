<script setup lang="ts">
    import type { Dtype, JsonSchemaPropertyConstraints } from "#shared/utils/schemas/types";
    import type { HTMLAttributes } from "vue";
    import {
        ArrowLeft,
        ChevronRight,
        Clock,
        Fingerprint,
        History,
        Key,
        Pencil,
        RotateCcw,
        Table2,
        Trash2,
    } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface ColumnBadge {
        icon?: Components.LucideIconComponent;
        label: string;
        class: HTMLAttributes["class"];
    }

    interface State {
        schemaCollapsibleOpen: boolean;
    }

    const { project, tables } = useProjectTabsSharedState();

    const state = useState<State>(
        NuxtKeys.Projects.Tables.State(project.value?.id, tables.state.value.selectedSchema),
        () => ({
            schemaCollapsibleOpen: false,
        }),
    );

    const tableName = computed(() => {
        if (!tables.state.value.selectedSchema) {
            return;
        }

        return TableUtils.getTableName(tables.state.value.selectedSchema.import_name);
    });

    const properties = computed(() => {
        if (!tables.state.value.selectedSchema) {
            return;
        }

        return Object.entries(tables.state.value.selectedSchema.active_schema.properties);
    });

    const sortedSchemaReleases = computed(() => {
        if (!tables.state.value.selectedSchema) {
            return;
        }

        return tables.state.value.selectedSchema.schemas_releases.toSorted(
            (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
    });

    const events = useAppEvents();
    function handleBack(_event: Event) {
        events.emit("event:projects:table:change-view", { value: "overview" });
    }

    function makeBadges(config: JsonSchemaPropertyConstraints): ColumnBadge[] {
        const badges: ColumnBadge[] = [];

        if (config.primary_key) {
            badges.push({
                label: "Primary",
                icon: Key,
                class: TableUtils.getPropertiesColor("primary"),
            });
        }

        if (config.unique && !config.primary_key) {
            badges.push({
                label: "Unique",
                icon: Fingerprint,
                class: TableUtils.getPropertiesColor("unique"),
            });
        }

        if (config.optional) {
            badges.push({ label: "Optional", class: TableUtils.getPropertiesColor("optional") });
        }

        return badges;
    }

    const animations = useCollapsibleAnimations();

    const { define: DefineTable, reuse: ReuseTable } = createReusableTemplate<{
        properties: [string, JsonSchemaPropertyConstraints & { type: Dtype }][];
    }>();

    const modal = useModal();

    function handleRevert(_event: Event) {
        if (!project.value) {
            return;
        }

        modal.dispatch.loadComponent({
            loader: () =>
                import("@/components/project/tables/ProjectTablesDeleteConfirmationModal.vue"),
            key: ModalKeys.Projects.Tables.Delete,
            props: {
                table: tables.state.value.selectedSchema,
                projectId: project.value.id,
                kind: "revert",
            },
        });
    }

    function handleDelete(_event: Event) {
        if (!project.value) {
            return;
        }

        modal.dispatch.loadComponent({
            loader: () =>
                import("@/components/project/tables/ProjectTablesDeleteConfirmationModal.vue"),
            key: ModalKeys.Projects.Tables.Delete,
            props: {
                table: tables.state.value.selectedSchema,
                projectId: project.value.id,
                kind: "delete",
                onSuccess: () => {},
            },
        });
    }
</script>

<template>
    <div>
        <DefineTable v-slot="{ properties: definedProperties }">
            <div class="rounded-lg border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableCell class="px-4 py-2">Column </TableCell>
                            <TableCell class="px-4 py-2">Type </TableCell>
                            <TableCell class="px-4 py-2">Constraints </TableCell>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <template v-for="[column, config] in definedProperties" :key="column">
                            <TableRow>
                                <TableCell class="px-4 font-mono text-sm text-foreground">
                                    {{ column }}
                                </TableCell>
                                <TableCell class="flex items-center space-x-2">
                                    <div
                                        :class="
                                            cn(
                                                'flex size-6 items-center justify-center rounded',
                                                TableUtils.getColor(config.type),
                                            )
                                        "
                                    >
                                        <component
                                            :is="TableUtils.getIcon(config.type)"
                                            class="size-3.5"
                                        />
                                    </div>
                                    <span class="text-sm text-muted-foreground">
                                        {{ config.type }}
                                    </span>
                                </TableCell>
                                <TableCell>
                                    <div class="w-full h-full flex flex-wrap items-center gap-1.5">
                                        <Badge
                                            v-for="badge in makeBadges({
                                                primary_key: config.primary_key || false,
                                                unique: config.unique || false,
                                                optional: config.optional || false,
                                            })"
                                            :key="badge.label"
                                            variant="outline"
                                            :class="cn(badge.class)"
                                        >
                                            <component :is="badge.icon" v-if="badge.icon" />
                                            {{ badge.label }}
                                        </Badge>
                                    </div>
                                </TableCell>
                            </TableRow>
                        </template>
                    </TableBody>
                </Table>
            </div>
        </DefineTable>

        <div class="flex flex-col space-y-6">
            <div class="flex items-center gap-4">
                <Button variant="ghost" size="icon" class="shrink-0" @click="handleBack">
                    <ArrowLeft class="size-4" />
                    <span class="sr-only">Back to tables</span>
                </Button>
                <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-3">
                        <div
                            class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10"
                        >
                            <Table2 class="size-5 text-primary" />
                        </div>
                        <div>
                            <h2 class="text-lg font-medium text-foreground">
                                {{ tableName }}
                            </h2>
                            <p class="text-xs text-muted-foreground font-mono">
                                {{ tables.state.value.selectedSchema?.id }}
                            </p>
                        </div>
                    </div>
                </div>

                <div class="space-x-2">
                    <Button v-if="project" variant="outline" as-child>
                        <NuxtLink
                            :to="
                                $localePath({
                                    name: 'projects-id-tables-tableName-edit',
                                    params: { id: project.id, tableName },
                                    query: {
                                        callbackUrl: $route.fullPath,
                                    },
                                })
                            "
                        >
                            <Pencil class="size-4" />
                            Edit Schema
                        </NuxtLink>
                    </Button>
                    <Button
                        v-if="sortedSchemaReleases"
                        variant="destructive"
                        :disabled="sortedSchemaReleases.length > 0"
                        @click="handleDelete"
                    >
                        <Trash2 class="size-4" />
                    </Button>
                </div>
            </div>

            <Card v-if="tables.state.value.selectedSchema" class="overflow-hidden">
                <CardHeader>
                    <CardTitle class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <Badge variant="default"> Active </Badge>
                            <span> {{ properties?.length }} columns </span>
                        </div>
                        <div class="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock class="size-3.5" />
                            {{
                                new Date(
                                    tables.state.value.selectedSchema.created_at,
                                ).toLocaleDateString($i18n.locale, {
                                    month: "short",
                                    day: "numeric",
                                    year: "numeric",
                                    hour: "2-digit",
                                    minute: "2-digit",
                                    timeZone: "UTC",
                                })
                            }}
                        </div>
                    </CardTitle>
                </CardHeader>

                <Separator />

                <CardContent class="space-y-4">
                    <div class="flex items-center space-x-2 text-xs text-muted-foreground">
                        <span class="font-medium">Schema:</span>
                        <code class="rounded bg-muted px-1.5 py-0.5">
                            {{ tables.state.value.selectedSchema.active_schema.$schema }}
                        </code>
                    </div>

                    <ReuseTable v-if="properties" :properties="properties" />

                    <Collapsible v-model:open="state.schemaCollapsibleOpen">
                        <Item class="bg-muted/30 py-1.5">
                            <ItemContent>
                                <ItemTitle> Raw JSON Schema </ItemTitle>
                            </ItemContent>
                            <ItemActions>
                                <CollapsibleTrigger as-child class="data-[state=open]:rotate-90">
                                    <Button variant="ghost" size="sm">
                                        <ChevronRight />
                                    </Button>
                                </CollapsibleTrigger>
                            </ItemActions>
                        </Item>
                        <Transition
                            :css="false"
                            @enter="animations.onEnter"
                            @leave="animations.onLeave"
                        >
                            <CollapsibleContent
                                v-if="state.schemaCollapsibleOpen"
                                force-mount
                                class="mt-4"
                            >
                                <CodeBlock
                                    :file="tableName"
                                    :content="tables.state.value.selectedSchema.active_schema"
                                />
                            </CollapsibleContent>
                        </Transition>
                    </Collapsible>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <History class="size-4 text-muted-foreground" />
                            <span class="text-sm font-medium text-foreground">Version History</span>
                        </div>
                        <div>
                            <Badge variant="secondary" class="text-xs font-normal">
                                {{ tables.state.value.selectedSchema?.schemas_releases.length }}
                                Releases
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
                                    <Item class="bg-muted/30">
                                        <ItemMedia>
                                            <Avatar>
                                                <AvatarFallback>
                                                    {{ `v${sortedSchemaReleases.length - index}` }}
                                                </AvatarFallback>
                                            </Avatar>
                                        </ItemMedia>
                                        <ItemContent>
                                            <ItemTitle>
                                                {{
                                                    Object.entries(release.schema.properties).length
                                                }}
                                                columns
                                            </ItemTitle>
                                        </ItemContent>
                                        <ItemActions>
                                            <div class="flex items-center space-x-2">
                                                <Button
                                                    v-if="index === 0"
                                                    size="sm"
                                                    variant="outline"
                                                    @click="handleRevert"
                                                >
                                                    <RotateCcw class="size-4" />
                                                    Revert
                                                </Button>
                                                <CollapsibleTrigger
                                                    as-child
                                                    class="data-[state=open]:rotate-90"
                                                >
                                                    <Button variant="ghost" size="sm">
                                                        <ChevronRight />
                                                    </Button>
                                                </CollapsibleTrigger>
                                            </div>
                                        </ItemActions>
                                    </Item>
                                    <Transition
                                        :css="false"
                                        @enter="animations.onEnter"
                                        @leave="animations.onLeave"
                                    >
                                        <CollapsibleContent v-if="open" force-mount class="mt-4">
                                            <div class="space-y-4">
                                                <ReuseTable
                                                    :properties="
                                                        Object.entries(release.schema.properties)
                                                    "
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
                                <EmptyTitle>No previous versions</EmptyTitle>
                                <EmptyDescription>
                                    Version history will appear here after updates.
                                </EmptyDescription>
                            </EmptyHeader>
                        </Empty>
                    </template>
                </CardContent>
            </Card>
        </div>
    </div>
</template>
