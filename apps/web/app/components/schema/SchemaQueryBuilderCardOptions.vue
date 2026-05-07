<script setup lang="ts">
    const qb = useQueryBuilder();
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle>
                {{ $t("projects.id.sections.query_builder.cards.options.title") }}
            </CardTitle>
            <CardDescription>
                {{ $t("projects.id.sections.query_builder.cards.options.description") }}
            </CardDescription>
        </CardHeader>
        <CardContent class="">
            <div class="flex flex-wrap items-center gap-4">
                <div class="flex items-center gap-2">
                    <Badge variant="secondary">
                        {{ $t("projects.id.sections.query_builder.labels.order_by") }}
                    </Badge>
                    <Select
                        :model-value="qb.state.orderBy.value.col || QB_ORDER_NONE"
                        @update:model-value="
                            qb.view.dispatch.onOrderByColChange($event?.toString())
                        "
                    >
                        <SelectTrigger class="h-8 w-36 font-mono text-xs">
                            <SelectValue
                                :placeholder="
                                    $t('projects.id.sections.query_builder.placeholders.order_none')
                                "
                            />
                        </SelectTrigger>
                        <SelectContent :body-lock="false">
                            <SelectItem :value="QB_ORDER_NONE">
                                {{
                                    $t("projects.id.sections.query_builder.placeholders.order_none")
                                }}
                            </SelectItem>
                            <SelectItem
                                v-for="col in qb.state.columnNames.value"
                                :key="col"
                                :value="col"
                            >
                                {{ col }}
                            </SelectItem>
                        </SelectContent>
                    </Select>
                    <Select v-model="qb.state.orderBy.value.dir">
                        <SelectTrigger class="h-8 w-24 font-mono text-xs">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent :body-lock="false">
                            <SelectItem value="ASC">ASC</SelectItem>
                            <SelectItem value="DESC">DESC</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div class="flex items-center gap-2">
                    <span class="text-xs text-muted-foreground">
                        {{ $t("projects.id.sections.query_builder.labels.limit") }}
                    </span>
                    <Input v-model.number="qb.state.limit.value" class="w-32" />
                </div>
            </div>
        </CardContent>
    </Card>
</template>
