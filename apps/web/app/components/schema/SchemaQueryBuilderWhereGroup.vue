<script setup lang="ts">
    import type {
        ConditionNode,
        ConditionOperator,
        GroupNode,
        LogicOperator,
    } from "~/composables/components/use-query-builder";
    import { Funnel, Plus, X } from "lucide-vue-next";
    import { OPS_MULTI_VALUE, OPS_NO_VALUE } from "~/composables/components/use-query-builder";
    import { cn } from "~/lib/utils";

    interface Props {
        group: GroupNode;
        columnNames: string[];
        opsForCol: (col: string) => ConditionOperator[];
        isRoot?: MaybeRefOrGetter<boolean>;
    }

    interface Emits {
        addCondition: [groupId: string | "root"];
        addGroup: [groupId: string | "root"];
        removeNode: [groupId: string];
        updateCondition: [
            nodeId: string,
            patch: Partial<Pick<ConditionNode, "col" | "op" | "val" | "conj">>,
        ];
        updateGroup: [nodeId: string, patch: Partial<Pick<GroupNode, "logic" | "conj">>];
        toggleConj: [nodeId: string];
    }

    const props = defineProps<Props>();
    const emit = defineEmits<Emits>();

    const isRoot = computed(() => toValue(props.isRoot));

    function needsValue(op: ConditionOperator) {
        return !OPS_NO_VALUE.includes(op);
    }

    function isMultiValue(op: ConditionOperator) {
        return OPS_MULTI_VALUE.includes(op);
    }

    function onColChange(node: ConditionNode, col: string | undefined) {
        if (!col) {
            return;
        }

        const ops = props.opsForCol(col);
        emit("updateCondition", node.id, { col, op: ops[0] ?? "=", val: "" });
    }

    function onOpChange(node: ConditionNode, op: ConditionOperator | undefined) {
        if (!op) {
            return;
        }

        emit("updateCondition", node.id, { op, val: "" });
    }

    function resolvePlaceholder(node: ConditionNode) {
        if (isMultiValue(node.op)) {
            return "projects.id.sections.query_builder.placeholders.multi_values";
        }

        return "projects.id.sections.query_builder.placeholders.value";
    }
    function forwardAddCondition(groupId: string | "root") {
        emit("addCondition", groupId);
    }

    function forwardAddGroup(groupId: string | "root") {
        emit("addGroup", groupId);
    }

    function forwardRemoveNode(groupId: string) {
        emit("removeNode", groupId);
    }

    function forwardUpdateCondition(
        nodeId: string,
        patch: Partial<Pick<ConditionNode, "col" | "op" | "val" | "conj">>,
    ) {
        emit("updateCondition", nodeId, patch);
    }

    function forwardUpdateGroup(nodeId: string, patch: Partial<Pick<GroupNode, "logic" | "conj">>) {
        emit("updateGroup", nodeId, patch);
    }

    function forwardToggleConj(nodeId: string) {
        emit("toggleConj", nodeId);
    }
</script>

<template>
    <div :class="cn('space-y-1.5', !isRoot && 'pl-4 border-l border-border ml-2')">
        <div v-if="!isRoot" class="flex space-x-4 items-center">
            <div class="flex items-center space-x-2">
                <Badge variant="secondary" class="">
                    {{ $t("projects.id.sections.query_builder.labels.group") }}
                </Badge>
                <Select
                    :model-value="group.logic"
                    @update:model-value="
                        emit('updateGroup', group.id, { logic: $event as LogicOperator })
                    "
                >
                    <SelectTrigger class="w-32">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent :body-lock="false">
                        <SelectItem value="AND">AND</SelectItem>
                        <SelectItem value="OR">OR</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <Button
                variant="ghost"
                size="icon"
                class="text-muted-foreground hover:text-destructive cursor-pointer"
                @click="emit('removeNode', group.id)"
            >
                <X />
            </Button>
        </div>

        <div class="space-y-4">
            <div class="space-y-2">
                <template v-for="(node, idx) in group.children" :key="node.id">
                    <div v-if="idx > 0" class="flex items-center">
                        <Tooltip :delay-duration="500">
                            <TooltipProvider>
                                <TooltipTrigger>
                                    <Button
                                        size="sm"
                                        class="cursor-pointer"
                                        @click="emit('toggleConj', node.id)"
                                    >
                                        {{ node.conj }}
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent side="right">
                                    {{
                                        $t(
                                            "projects.id.sections.query_builder.actions.toggle_conjunction",
                                        )
                                    }}
                                </TooltipContent>
                            </TooltipProvider>
                        </Tooltip>
                    </div>

                    <div
                        v-if="node.type === 'condition'"
                        class="flex flex-wrap items-center gap-1.5"
                    >
                        <Select
                            :model-value="node.col"
                            @update:model-value="onColChange(node, $event?.toString())"
                        >
                            <SelectTrigger class="h-8 w-36">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent :body-lock="false">
                                <SelectItem v-for="col in columnNames" :key="col" :value="col">
                                    {{ col }}
                                </SelectItem>
                            </SelectContent>
                        </Select>

                        <Select
                            :model-value="node.op"
                            @update:model-value="
                                onOpChange(
                                    node,
                                    $event?.toString() as ConditionOperator | undefined,
                                )
                            "
                        >
                            <SelectTrigger class="h-8 w-32">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent :body-lock="false">
                                <SelectItem v-for="op in opsForCol(node.col)" :key="op" :value="op">
                                    {{ op }}
                                </SelectItem>
                            </SelectContent>
                        </Select>

                        <Input
                            v-if="needsValue(node.op)"
                            :model-value="node.val"
                            :placeholder="$t(resolvePlaceholder(node))"
                            :class="
                                cn(
                                    'w-64',
                                    !node.val.length &&
                                        'border-destructive focus-visible:ring-destructive focus-visible:ring-2',
                                )
                            "
                            @update:model-value="
                                emit('updateCondition', node.id, { val: $event.toString() })
                            "
                        />

                        <Button
                            variant="ghost"
                            size="icon"
                            class="h-7 w-7 text-muted-foreground hover:text-destructive"
                            @click="emit('removeNode', node.id)"
                        >
                            <X />
                        </Button>
                    </div>

                    <div v-else-if="node.type === 'group'" class="space-y-3">
                        <SchemaQueryBuilderWhereGroup
                            :group="node"
                            :column-names="columnNames"
                            :ops-for-col="opsForCol"
                            :is-root="false"
                            @add-condition="forwardAddCondition"
                            @add-group="forwardAddGroup"
                            @remove-node="forwardRemoveNode"
                            @update-condition="forwardUpdateCondition"
                            @update-group="forwardUpdateGroup"
                            @toggle-conj="forwardToggleConj"
                        >
                            <template #controls>
                                <slot name="controls" />
                            </template>
                        </SchemaQueryBuilderWhereGroup>
                        <div class="flex space-x-2 pl-6">
                            <Button
                                variant="outline"
                                size="sm"
                                @click="emit('addCondition', node.id)"
                            >
                                <Plus />
                                {{ $t("projects.id.sections.query_builder.actions.add_condition") }}
                            </Button>
                            <Button variant="outline" size="sm" @click="emit('addGroup', node.id)">
                                <Plus />
                                {{ $t("projects.id.sections.query_builder.actions.add_group") }}
                            </Button>
                        </div>
                    </div>
                </template>
            </div>
            <template v-if="isRoot && !!group.children.length">
                <slot name="controls" />
            </template>
        </div>

        <template v-if="isRoot && !group.children.length">
            <Empty>
                <EmptyHeader>
                    <EmptyMedia variant="icon">
                        <Funnel />
                    </EmptyMedia>
                    <EmptyTitle>
                        {{ $t("projects.id.sections.query_builder.empty.no_conditions") }}
                    </EmptyTitle>
                </EmptyHeader>
                <EmptyContent>
                    <slot name="controls" />
                </EmptyContent>
            </Empty>
        </template>

        <template v-if="!isRoot && !group.children.length">
            <p class="text-xs text-muted-foreground py-1">
                {{ $t("projects.id.sections.query_builder.empty.no_conditions") }}
            </p>
        </template>
    </div>
</template>
