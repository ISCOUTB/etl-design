import type { Dtype, JsonSchema } from "#shared/utils/schemas/types";
import type { Knex } from "knex";
import { v7 } from "uuid";

export const QB_DTYPE_TO_PG: Record<Dtype, string> = {
    string: "text",
    integer: "integer",
    boolean: "boolean",
    double: "numeric",
    float: "numeric",
};

export const QB_OPS_NO_VALUE: Components.QueryBuilder.Operators.ConditionOperator[] = [
    "IS NULL",
    "IS NOT NULL",
];
export const QB_OPS_MULTI_VALUE: Components.QueryBuilder.Operators.ConditionOperator[] = [
    "IN",
    "NOT IN",
];
export const QB_ORDER_NONE = "__none__";

export const QB_OPS_BY_PG: Record<string, Components.QueryBuilder.Operators.ConditionOperator[]> = {
    text: ["=", "!=", "LIKE", "ILIKE", "IN", "NOT IN", "IS NULL", "IS NOT NULL"],
    numeric: ["=", "!=", ">", "<", ">=", "<=", "IS NULL", "IS NOT NULL"],
    integer: ["=", "!=", ">", "<", ">=", "<=", "IN", "NOT IN", "IS NULL", "IS NOT NULL"],
    boolean: ["=", "!=", "IS NULL", "IS NOT NULL"],
    jsonb: ["IS NULL", "IS NOT NULL"],
};

export const QB_NO_VALUE_OPS = new Set<Components.QueryBuilder.Operators.ConditionOperator>([
    "IS NULL",
    "IS NOT NULL",
]);

export const QB_MULTI_VALUE_OPS = new Set<Components.QueryBuilder.Operators.ConditionOperator>([
    "IN",
    "NOT IN",
]);

function standardizeWhereNode(
    node: Components.QueryBuilder.Nodes.GroupNode,
    standardize: (string: string) => string,
): Components.QueryBuilder.Nodes.GroupNode;
function standardizeWhereNode(
    node: Components.QueryBuilder.Nodes.ConditionNode,
    standardize: (string: string) => string,
): Components.QueryBuilder.Nodes.ConditionNode;
function standardizeWhereNode(
    node: Components.QueryBuilder.Nodes.QueryNode,
    standardize: (string: string) => string,
): Components.QueryBuilder.Nodes.QueryNode;
function standardizeWhereNode(
    node: Components.QueryBuilder.Nodes.QueryNode,
    standardize: (string: string) => string,
): Components.QueryBuilder.Nodes.QueryNode {
    if (node.type === "group" && Array.isArray(node.children)) {
        return {
            ...node,
            children: node.children.map((child) => standardizeWhereNode(child, standardize)),
        };
    }

    if (node.type === "condition") {
        return {
            ...node,
            col: standardize(node.col),
        };
    }

    return node;
}

export const QueryBuilderUtils = {
    options: {
        forColumn(
            col: Components.QueryBuilder.KnexColumn,
        ): Components.QueryBuilder.Operators.ConditionOperator[] {
            return QB_OPS_BY_PG[col.pgType] ?? ["=", "!=", "IS NULL", "IS NOT NULL"];
        },
    },

    tree: {
        makeCondition(
            col: string,
            conj: Components.QueryBuilder.Operators.LogicOperator = "AND",
        ): Components.QueryBuilder.Nodes.ConditionNode {
            return { id: v7(), type: "condition", col, op: "=", val: "", conj };
        },

        makeGroup(
            logic: Components.QueryBuilder.Operators.LogicOperator = "AND",
            conj: Components.QueryBuilder.Operators.LogicOperator = "AND",
        ): Components.QueryBuilder.Nodes.GroupNode {
            return { id: v7(), type: "group", logic, children: [], conj };
        },

        findNode(
            group: Components.QueryBuilder.Nodes.GroupNode,
            targetId: string,
        ): Components.QueryBuilder.Nodes.QueryNode | null {
            for (const child of group.children) {
                if (child.id === targetId) {
                    return child;
                }

                if (child.type === "group") {
                    const r = QueryBuilderUtils.tree.findNode(child, targetId);
                    if (r) {
                        return r;
                    }
                }
            }
            return null;
        },

        findAndRemove(group: Components.QueryBuilder.Nodes.GroupNode, targetId: string): boolean {
            const idx = group.children.findIndex((n) => n.id === targetId);
            if (idx !== -1) {
                group.children.splice(idx, 1);
                return true;
            }
            for (const child of group.children) {
                if (
                    child.type === "group" &&
                    QueryBuilderUtils.tree.findAndRemove(child, targetId)
                ) {
                    return true;
                }
            }
            return false;
        },
    },

    knex: {
        applyGroup(
            builder: Knex.QueryBuilder,
            group: Components.QueryBuilder.Nodes.GroupNode,
        ): void {
            group.children.forEach((node, i) => {
                const isFirst = i === 0;
                const useOr = !isFirst && node.conj === "OR";

                if (node.type === "condition") {
                    QueryBuilderUtils.knex.applyCondition(builder, node, useOr);
                    return;
                }

                if (isFirst) {
                    builder.where((sub) => QueryBuilderUtils.knex.applyGroup(sub, node));
                    return;
                }

                if (useOr) {
                    builder.orWhere((sub) => QueryBuilderUtils.knex.applyGroup(sub, node));
                    return;
                }

                builder.andWhere((sub) => QueryBuilderUtils.knex.applyGroup(sub, node));
            });
        },

        applyNullCondition(
            builder: Knex.QueryBuilder,
            col: string,
            op: Components.QueryBuilder.Operators.ConditionOperator,
            useOr: boolean,
        ): boolean {
            if (op === "IS NULL") {
                useOr ? builder.orWhereNull(col) : builder.whereNull(col);
                return true;
            }

            if (op === "IS NOT NULL") {
                if (useOr) {
                    builder.orWhereNotNull(col);
                    return true;
                }

                builder.whereNotNull(col);
                return true;
            }

            return false;
        },

        applySetCondition(
            builder: Knex.QueryBuilder,
            col: string,
            op: Components.QueryBuilder.Operators.ConditionOperator,
            val: string,
            useOr: boolean,
        ): boolean {
            if (op !== "IN" && op !== "NOT IN") {
                return false;
            }

            const values = val
                .split(",")
                .map((v) => v.trim())
                .filter(Boolean);

            if (op === "IN") {
                useOr ? builder.orWhereIn(col, values) : builder.whereIn(col, values);
                return true;
            }

            if (useOr) {
                builder.orWhereNotIn(col, values);
                return true;
            }

            builder.whereNotIn(col, values);
            return true;
        },

        applyLikeCondition(
            builder: Knex.QueryBuilder,
            col: string,
            op: Components.QueryBuilder.Operators.ConditionOperator,
            val: string,
            useOr: boolean,
        ): boolean {
            if (op !== "LIKE" && op !== "ILIKE") {
                return false;
            }

            if (useOr) {
                builder.orWhereRaw(`?? ${op} ?`, [col, val]);
                return true;
            }

            builder.whereRaw(`?? ${op} ?`, [col, val]);
            return true;
        },

        applyCondition(
            builder: Knex.QueryBuilder,
            node: Components.QueryBuilder.Nodes.ConditionNode,
            useOr: boolean,
        ): void {
            const { col, op, val } = node;

            if (QueryBuilderUtils.knex.applyNullCondition(builder, col, op, useOr)) {
                return;
            }

            if (QueryBuilderUtils.knex.applySetCondition(builder, col, op, val, useOr)) {
                return;
            }

            if (QueryBuilderUtils.knex.applyLikeCondition(builder, col, op, val, useOr)) {
                return;
            }

            if (useOr) {
                builder.orWhere(col, op, val);
                return;
            }

            builder.andWhere(col, op, val);
        },
    },

    mongoSchemaToColumns(schema: JsonSchema) {
        const required = schema.required ?? [];

        return Object.entries(schema.properties).map<Components.QueryBuilder.KnexColumn>(
            ([name, def]) => ({
                name,
                pgType: QB_DTYPE_TO_PG[def.type],
                nullable: !required.includes(name),
                required: required.includes(name),
                dtype: def.type,
            }),
        );
    },

    validate: {
        scalarByType(dtype: Dtype, value: string, onError: () => void) {
            if (dtype === "integer") {
                if (!/^-?\d+$/.test(value)) {
                    onError();
                }
                return;
            }

            if (dtype === "float" || dtype === "double") {
                if (!Number.isFinite(Number(value))) {
                    onError();
                }
                return;
            }

            if (dtype === "boolean") {
                if (!["true", "false", "1", "0"].includes(value.toLowerCase())) {
                    onError();
                }
            }
        },

        node(
            node: Components.QueryBuilder.Nodes.QueryNode,
            columnsByName: Map<string, Components.QueryBuilder.KnexColumn>,
            onError: () => void,
        ) {
            if (node.type === "group") {
                for (const child of node.children) {
                    QueryBuilderUtils.validate.node(child, columnsByName, onError);
                }

                return;
            }

            const column = columnsByName.get(node.col);
            if (!column) {
                throw createError({
                    status: 400,
                    statusText: ResponseCodesRecord.Server.Project.QueryBuilder.InvalidColumns,
                });
            }

            const allowedOps = QueryBuilderUtils.options.forColumn(column);
            if (!allowedOps.includes(node.op)) {
                onError();
            }

            if (QB_NO_VALUE_OPS.has(node.op)) {
                return;
            }

            const raw = node.val.trim() ?? "";
            if (!raw.length) {
                onError();
            }

            if (QB_MULTI_VALUE_OPS.has(node.op)) {
                const values = raw
                    .split(",")
                    .map((value) => value.trim())
                    .filter(Boolean);

                if (!values.length) {
                    onError();
                }

                for (const value of values) {
                    QueryBuilderUtils.validate.scalarByType(column.dtype, value, onError);
                }

                return;
            }

            QueryBuilderUtils.validate.scalarByType(column.dtype, raw, onError);
        },

        groupNode(
            columns: Components.QueryBuilder.KnexColumn[],
            tree: Components.QueryBuilder.Nodes.GroupNode,
        ) {
            const columnsByName = new Map(columns.map((column) => [column.name, column]));

            function panic() {
                throw createError({
                    status: 400,
                    statusText: ResponseCodesRecord.Server.BadPayload,
                });
            }

            QueryBuilderUtils.validate.node(tree, columnsByName, panic);
        },
    },

    standardize: {
        normalize(string: string): string {
            return string
                .toLowerCase()
                .trim()
                .normalize("NFD")
                .replace(/[\u0300-\u036F]/g, "")
                .replace(/\s+/g, "_");
        },

        where: standardizeWhereNode,
    },
};
