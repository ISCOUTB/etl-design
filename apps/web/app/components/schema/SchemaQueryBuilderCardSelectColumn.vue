<script setup lang="ts">
    import { Grid2x2Check, Grid2x2X, Plus, X } from "lucide-vue-next";

    const qb = useQueryBuilder();
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle>
                {{ $t("projects.id.sections.query_builder.cards.columns.title") }}
            </CardTitle>
            <CardDescription>
                {{ $t("projects.id.sections.query_builder.cards.columns.description") }}
            </CardDescription>
        </CardHeader>
        <CardContent>
            <template v-if="qb.state.selectedCols.value.length > 0">
                <div class="space-y-6">
                    <div class="space-y-4">
                        <div
                            v-for="(sc, i) in qb.state.selectedCols.value"
                            :key="sc.id"
                            class="flex items-center space-x-4"
                        >
                            <span
                                class="text-sm text-muted-foreground w-5 text-right cursor-default select-none"
                            >
                                {{ i + 1 }}
                            </span>

                            <Select
                                :model-value="sc.col"
                                @update:model-value="
                                    qb.dispatch.updateColumn(sc.id, $event?.toString())
                                "
                            >
                                <SelectTrigger class="h-8 w-44 font-mono text-xs">
                                    <SelectValue
                                        :placeholder="
                                            $t(
                                                'projects.id.sections.query_builder.placeholders.select_column',
                                            )
                                        "
                                    />
                                </SelectTrigger>
                                <SelectContent :body-lock="false">
                                    <SelectItem
                                        v-for="col in qb.state.columnNames.value"
                                        :key="col"
                                        :value="col"
                                    >
                                        {{ col }}
                                    </SelectItem>
                                </SelectContent>
                            </Select>

                            <div class="w-28">
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger>
                                            <Badge variant="outline" class="cursor-default">
                                                {{
                                                    qb.state.columns.value.find(
                                                        (c) => c.name === sc.col,
                                                    )?.pgType ?? "?"
                                                }}
                                            </Badge>
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p class="text-xs">
                                                {{
                                                    $t(
                                                        "projects.id.sections.query_builder.labels.dtype",
                                                    )
                                                }}:
                                                {{
                                                    qb.state.columns.value.find(
                                                        (c) => c.name === sc.col,
                                                    )?.dtype
                                                }}
                                            </p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            </div>

                            <Button
                                variant="ghost"
                                size="icon"
                                class="h-9 text-muted-foreground hover:text-destructive cursor-pointer"
                                @click="qb.dispatch.removeColumn(sc.id)"
                            >
                                <X />
                            </Button>
                        </div>
                    </div>

                    <div class="flex items-center space-x-2">
                        <Button variant="outline" @click="qb.dispatch.addColumn">
                            <Plus />
                            {{ $t("projects.id.sections.query_builder.actions.add_column") }}
                        </Button>

                        <Button
                            variant="default"
                            class="cursor-pointer"
                            @click="qb.dispatch.selectAllColumns()"
                        >
                            <Grid2x2Check />
                            {{ $t("projects.id.sections.query_builder.actions.select_all") }}
                        </Button>
                    </div>
                </div>
            </template>

            <Empty v-if="!qb.state.selectedCols.value.length">
                <EmptyHeader>
                    <EmptyMedia variant="icon">
                        <Grid2x2X />
                    </EmptyMedia>
                    <EmptyTitle>
                        {{ $t("projects.id.sections.query_builder.empty.header.title") }}
                    </EmptyTitle>
                    <EmptyDescription>
                        {{ $t("projects.id.sections.query_builder.empty.header.description") }}
                    </EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                    <div>
                        <Button
                            variant="outline"
                            size="sm"
                            class="cursor-pointer"
                            @click="qb.dispatch.addColumn"
                        >
                            <Plus />
                            {{ $t("projects.id.sections.query_builder.actions.add_column") }}
                        </Button>
                    </div>
                </EmptyContent>
            </Empty>
        </CardContent>
    </Card>
</template>
