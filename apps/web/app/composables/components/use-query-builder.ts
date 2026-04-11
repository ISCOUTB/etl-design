import type { JsonSchema, MongoRaw } from "#shared/utils/schemas/types";
import { knex } from "knex";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface JsonSchemaProperty {
    type: Dtype;
    [key: string]: unknown;
}

interface KnexColumnInfo {
    name: string;
    pgType: string;
    nullable: boolean;
    required: boolean;
    dtype: Dtype;
}

export interface ConditionNode {
    id: string;
    type: "condition";
    col: string;
    op: ConditionOperator;
    val: string;
    conj: LogicOperator;
}

export interface GroupNode {
    id: string;
    type: "group";
    logic: LogicOperator;
    children: QueryNode[];
    conj: LogicOperator;
}

export type QueryNode = ConditionNode | GroupNode;

export interface ColumnSelection {
    id: string;
    col: string;
}

export interface OrderByState {
    col: string;
    dir: "ASC" | "DESC";
}

export interface KnexQueryOutput {
    sql: string;
    bindings: readonly unknown[];
}

export type ConditionOperator =
    | "="
    | "!="
    | ">"
    | "<"
    | ">="
    | "<="
    | "LIKE"
    | "ILIKE"
    | "IN"
    | "NOT IN"
    | "IS NULL"
    | "IS NOT NULL";

export type LogicOperator = "AND" | "OR";

// ─── Constants ────────────────────────────────────────────────────────────────

const DTYPE_TO_PG: Record<Dtype, string> = {
    string: "text",
    integer: "integer",
    boolean: "boolean",
    double: "numeric",
    float: "numeric",
};

export const OPS_NO_VALUE: ConditionOperator[] = ["IS NULL", "IS NOT NULL"];
export const OPS_MULTI_VALUE: ConditionOperator[] = ["IN", "NOT IN"];
const ORDER_NONE = "__none__";

const OPS_BY_PG: Record<string, ConditionOperator[]> = {
    text: ["=", "!=", "LIKE", "ILIKE", "IN", "NOT IN", "IS NULL", "IS NOT NULL"],
    numeric: ["=", "!=", ">", "<", ">=", "<=", "IS NULL", "IS NOT NULL"],
    integer: ["=", "!=", ">", "<", ">=", "<=", "IN", "NOT IN", "IS NULL", "IS NOT NULL"],
    boolean: ["=", "!=", "IS NULL", "IS NOT NULL"],
    jsonb: ["IS NULL", "IS NOT NULL"],
};

// ─── Knex ─────────────────────────────────────────────────────────────────────

const qb = knex({ client: "pg" });
type QB = ReturnType<typeof qb.queryBuilder>;

// ─── Schema helpers ───────────────────────────────────────────────────────────

function mongoSchemaToColumns(schema: JsonSchema) {
    const required = schema.required ?? [];

    return Object.entries(schema.properties).map<KnexColumnInfo>(([name, def]) => ({
        name,
        pgType: DTYPE_TO_PG[def.type],
        nullable: !required.includes(name),
        required: required.includes(name),
        dtype: def.type,
    }));
}

function opsForColumn(col: KnexColumnInfo): ConditionOperator[] {
    return OPS_BY_PG[col.pgType] ?? ["=", "!=", "IS NULL", "IS NOT NULL"];
}

// ─── Tree helpers ─────────────────────────────────────────────────────────────

let _id = 0;
function uid(): string {
    return `n${++_id}`;
}

function makeCondition(col: string, conj: LogicOperator = "AND"): ConditionNode {
    return { id: uid(), type: "condition", col, op: "=", val: "", conj };
}

function makeGroup(logic: LogicOperator = "AND", conj: LogicOperator = "AND"): GroupNode {
    return { id: uid(), type: "group", logic, children: [], conj };
}

function findNode(group: GroupNode, targetId: string): QueryNode | null {
    for (const child of group.children) {
        if (child.id === targetId) {
            return child;
        }

        if (child.type === "group") {
            const r = findNode(child, targetId);
            if (r) {
                return r;
            }
        }
    }
    return null;
}

function findAndRemove(group: GroupNode, targetId: string): boolean {
    const idx = group.children.findIndex((n) => n.id === targetId);
    if (idx !== -1) {
        group.children.splice(idx, 1);
        return true;
    }
    for (const child of group.children) {
        if (child.type === "group" && findAndRemove(child, targetId)) {
            return true;
        }
    }
    return false;
}

// ─── Knex where builder ───────────────────────────────────────────────────────

function applyGroup(builder: QB, group: GroupNode): void {
    group.children.forEach((node, i) => {
        const isFirst = i === 0;
        const useOr = !isFirst && node.conj === "OR";

        if (node.type === "condition") {
            applyCondition(builder, node, useOr);
            return;
        }

        if (isFirst) {
            builder.where((sub) => applyGroup(sub, node));
            return;
        }
        if (useOr) {
            builder.orWhere((sub) => applyGroup(sub, node));
            return;
        }
        builder.andWhere((sub) => applyGroup(sub, node));
    });
}

function applyNullCondition(
    builder: QB,
    col: string,
    op: ConditionOperator,
    useOr: boolean,
): boolean {
    if (op === "IS NULL") {
        useOr ? builder.orWhereNull(col) : builder.whereNull(col);
        return true;
    }

    if (op === "IS NOT NULL") {
        useOr ? builder.orWhereNotNull(col) : builder.whereNotNull(col);
        return true;
    }

    return false;
}

function applySetCondition(
    builder: QB,
    col: string,
    op: ConditionOperator,
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

    useOr ? builder.orWhereNotIn(col, values) : builder.whereNotIn(col, values);
    return true;
}

function applyLikeCondition(
    builder: QB,
    col: string,
    op: ConditionOperator,
    val: string,
    useOr: boolean,
): boolean {
    if (op !== "LIKE" && op !== "ILIKE") {
        return false;
    }

    useOr
        ? builder.orWhereRaw(`?? ${op} ?`, [col, val])
        : builder.whereRaw(`?? ${op} ?`, [col, val]);
    return true;
}

function applyCondition(builder: QB, node: ConditionNode, useOr: boolean): void {
    const { col, op, val } = node;

    if (applyNullCondition(builder, col, op, useOr)) {
        return;
    }

    if (applySetCondition(builder, col, op, val, useOr)) {
        return;
    }

    if (applyLikeCondition(builder, col, op, val, useOr)) {
        return;
    }

    useOr ? builder.orWhere(col, op, val) : builder.andWhere(col, op, val);
}

export const [useProvideQueryBuilderApi, _useQueryBuilderApi] = createInjectionState(
    (schema: MaybeRefOrGetter<MongoRaw>) => {
        const activeSchema = computed(() => toValue(schema));

        const importName = computed(() => activeSchema.value?.import_name ?? "");

        const columns = computed<KnexColumnInfo[]>(() => {
            if (activeSchema.value) {
                return mongoSchemaToColumns(activeSchema.value.active_schema);
            }

            return [];
        });

        const columnNames = computed(() => columns.value.map((c) => c.name));

        function getColumn(name: string): KnexColumnInfo | undefined {
            return columns.value.find((c) => c.name === name);
        }

        function opsForCol(colName: string): ConditionOperator[] {
            const col = getColumn(colName);
            if (col) {
                return opsForColumn(col);
            }

            return ["=", "!=", "IS NULL", "IS NOT NULL"];
        }

        const selectedCols = useState<ColumnSelection[]>(
            NuxtKeys.Components.QueryBuilder.SelectedColumns(activeSchema.value),
            () => [],
        );
        const whereTree = useState<GroupNode>(
            NuxtKeys.Components.QueryBuilder.WhereTree(activeSchema.value),
            () => makeGroup("AND"),
        );
        const orderBy = useState<OrderByState>(
            NuxtKeys.Components.QueryBuilder.OrderBy(activeSchema.value),
            () => ({
                col: "",
                dir: "ASC",
            }),
        );
        const limit = useState<number | undefined>(
            NuxtKeys.Components.QueryBuilder.Limit(activeSchema.value),
            () => undefined,
        );

        watch(
            () => importName.value,
            () => {
                selectedCols.value = [];
                whereTree.value = makeGroup("AND");
                orderBy.value = { col: "", dir: "ASC" };
                limit.value = 100;
            },
        );

        // ── Column actions ───────────────────────────────────────────────────────

        function addColumn() {
            selectedCols.value.push({ id: uid(), col: columnNames.value[0] ?? "" });
        }

        function removeColumn(id: string) {
            selectedCols.value = selectedCols.value.filter((c) => c.id !== id);
        }

        function selectAllColumns() {
            selectedCols.value.length = 0;
        }

        function updateColumn(id: string, col: string | undefined) {
            const t = selectedCols.value.find((c) => c.id === id);
            if (!t || !col) {
                return;
            }

            t.col = col;
        }

        // ── Where actions ────────────────────────────────────────────────────────

        function resolveGroup(groupId: string | "root"): GroupNode | null {
            if (groupId === "root") {
                return whereTree.value;
            }
            const node = findNode(whereTree.value, groupId);

            if (node?.type === "group") {
                return node;
            }

            return null;
        }

        function addConditionTo(groupId: string | "root") {
            const group = resolveGroup(groupId);
            if (!group) {
                return;
            }
            group.children.push(makeCondition(columnNames.value[0] ?? "", "AND"));
        }

        function addGroupTo(groupId: string | "root") {
            const group = resolveGroup(groupId);
            if (!group) {
                return;
            }
            group.children.push(makeGroup("AND", "AND"));
        }

        function removeNode(nodeId: string) {
            findAndRemove(whereTree.value, nodeId);
        }

        function removeAllNodes() {
            whereTree.value.children.length = 0;
        }

        function updateCondition(
            nodeId: string,
            patch: Partial<Pick<ConditionNode, "col" | "op" | "val" | "conj">>,
        ) {
            const node = findNode(whereTree.value, nodeId);
            if (node?.type === "condition") {
                Object.assign(node, patch);
            }
        }

        function updateGroup(nodeId: string, patch: Partial<Pick<GroupNode, "logic" | "conj">>) {
            const node = findNode(whereTree.value, nodeId);
            if (node?.type === "group") {
                Object.assign(node, patch);
            }
        }

        function toggleConj(nodeId: string) {
            const node = findNode(whereTree.value, nodeId);
            if (node) {
                if (node.conj === "AND") {
                    node.conj = "OR";
                    return;
                }

                node.conj = "AND";
            }
        }

        function reset() {
            selectedCols.value = [];
            whereTree.value = makeGroup("AND");
            orderBy.value = { col: "", dir: "ASC" };
            limit.value = 100;
        }

        // ── Outputs ──────────────────────────────────────────────────────────────

        const queryOutput = computed<KnexQueryOutput | null>(() => {
            if (!activeSchema.value || !importName.value) {
                return null;
            }

            const cols = selectedCols.value.length ? selectedCols.value.map((c) => c.col) : ["*"];

            const builder = qb(TableUtils.getTableName(importName.value)).select(cols);

            if (whereTree.value.children.length)
                builder.where((sub) => applyGroup(sub as unknown as QB, whereTree.value));

            if (orderBy.value.col) {
                builder.orderBy(orderBy.value.col, orderBy.value.dir);
            }

            if (limit.value) {
                builder.limit(limit.value);
            }

            const native = builder.toSQL().toNative();
            return { sql: native.sql, bindings: native.bindings };
        });

        const generatedSQL = computed<string>(() => {
            if (!queryOutput.value) {
                return "";
            }
            const { sql, bindings } = queryOutput.value;
            return bindings.reduce<string>(
                (acc, val, i) =>
                    acc.replace(`$${i + 1}`, typeof val === "string" ? `'${val}'` : String(val)),
                sql,
            );
        });

        const queryTree = computed(() => {
            if (!activeSchema.value || !importName.value) {
                return null;
            }
            return {
                table: TableUtils.getTableName(importName.value),
                select: selectedCols.value.length ? selectedCols.value.map((c) => c.col) : ["*"],
                where: whereTree.value,
                orderBy: orderBy.value.col ? orderBy.value : null,
                limit: limit.value,
            };
        });

        return {
            state: {
                activeSchema,
                columns,
                columnNames,
                selectedCols,
                whereTree,
                orderBy,
                limit,
            },
            dispatch: {
                opsForCol,
                getColumn,
                addColumn,
                removeColumn,
                selectAllColumns,
                updateColumn,
                addConditionTo,
                addGroupTo,
                removeNode,
                removeAllNodes,
                updateCondition,
                updateGroup,
                toggleConj,
                reset,
            },
            computed: {
                queryOutput,
                generatedSQL,
                queryTree,
            },
        };
    },
);

export const [useProvideQueryBuilderView, _useQueryBuilderView] = createInjectionState(
    (qb: NonNullable<ReturnType<typeof _useQueryBuilderApi>>) => {
        const clipboard = useClipboard();

        const output = computed(() => ({
            sql: qb.computed.generatedSQL.value,
            native: JSON.stringify(qb.computed.queryOutput.value, null, 2),
            tree: JSON.stringify(qb.computed.queryTree.value, null, 2),
        }));

        function onOrderByColChange(payload?: string) {
            const value = payload?.toString() ?? ORDER_NONE;
            qb.state.orderBy.value.col = value === ORDER_NONE ? "" : value;
        }

        return {
            ORDER_NONE,
            state: {
                clipboard,
            },
            dispatch: {
                onOrderByColChange,
            },
            computed: {
                output,
            },
        };
    },
);

export const [useProvideQueryBuilder, _useQueryBuilder] = createInjectionState(
    (schema: MaybeRefOrGetter<MongoRaw>) => {
        const api = useProvideQueryBuilderApi(schema);
        const view = useProvideQueryBuilderView(api);

        return {
            ...api,
            view,
        };
    },
);

export function useQueryBuilder() {
    const state = _useQueryBuilder();
    if (!state) {
        throw createError({
            status: 500,
            statusText: "QueryBuilder status is not injected",
            fatal: true,
        });
    }
    return state;
}
