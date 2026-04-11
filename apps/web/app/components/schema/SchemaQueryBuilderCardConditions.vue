<script setup lang="ts">
    import { Plus, RotateCcw } from "lucide-vue-next";

    const qb = useQueryBuilder();
</script>

<template>
    <Card>
        <CardHeader>
            <div class="flex items-center justify-between">
                <div class="space-y-1.5">
                    <CardTitle>
                        {{ $t("projects.id.sections.query_builder.cards.where.title") }}
                    </CardTitle>
                    <CardDescription>
                        {{ $t("projects.id.sections.query_builder.cards.where.description") }}
                    </CardDescription>
                </div>

                <div>
                    <Button
                        variant="outline"
                        class="cursor-pointer"
                        @click="qb.dispatch.removeAllNodes()"
                    >
                        <RotateCcw /> Reset
                    </Button>
                </div>
            </div>
        </CardHeader>
        <CardContent>
            <SchemaQueryBuilderWhereGroup
                :group="qb.state.whereTree.value"
                :column-names="qb.state.columnNames.value"
                :ops-for-col="qb.dispatch.opsForCol"
                :is-root="true"
                @add-condition="qb.dispatch.addConditionTo"
                @add-group="qb.dispatch.addGroupTo"
                @remove-node="qb.dispatch.removeNode"
                @update-condition="qb.dispatch.updateCondition"
                @update-group="qb.dispatch.updateGroup"
                @toggle-conj="qb.dispatch.toggleConj"
            >
                <template #controls>
                    <div class="flex flex-wrap space-x-2">
                        <Button
                            variant="outline"
                            size="sm"
                            @click="qb.dispatch.addConditionTo('root')"
                        >
                            <Plus />
                            {{ $t("projects.id.sections.query_builder.actions.add_condition") }}
                        </Button>
                        <Button variant="outline" size="sm" @click="qb.dispatch.addGroupTo('root')">
                            <Plus />
                            {{ $t("projects.id.sections.query_builder.actions.add_group") }}
                        </Button>
                    </div>
                </template>
            </SchemaQueryBuilderWhereGroup>
        </CardContent>
    </Card>
</template>
