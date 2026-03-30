<script setup lang="ts">
    import { ChevronsRight, Clock } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface State {
        schemaCollapsibleOpen: boolean;
    }

    const { tables, project } = useProjectTabsSharedState();

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

    const animations = useCollapsibleAnimations();
</script>

<template>
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
                        new Date(tables.state.value.selectedSchema.created_at).toLocaleDateString(
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

            <ProjectTablesSchemaDetailsTable v-if="properties" :properties="properties" />

            <Collapsible v-slot="{ open }" v-model:open="state.schemaCollapsibleOpen">
                <CollapsibleTrigger as-child>
                    <Item class="bg-muted/30 h-12 py-1.5 cursor-pointer">
                        <ItemContent>
                            <ItemTitle> Raw JSON Schema </ItemTitle>
                        </ItemContent>
                        <ItemActions>
                            <ChevronsRight :class="cn('size-5 transition-transform', open && 'rotate-90')" />
                        </ItemActions>
                    </Item>
                </CollapsibleTrigger>
                <Transition :css="false" @enter="animations.onEnter" @leave="animations.onLeave">
                    <CollapsibleContent v-if="state.schemaCollapsibleOpen" force-mount class="mt-4">
                        <CodeBlock
                            :file="tableName"
                            :content="tables.state.value.selectedSchema.active_schema"
                        />
                    </CollapsibleContent>
                </Transition>
            </Collapsible>
        </CardContent>
    </Card>
</template>
