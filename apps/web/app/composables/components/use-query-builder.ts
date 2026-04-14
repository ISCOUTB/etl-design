import type { MongoRaw } from "#shared/utils/schemas/types";
import type { Knex } from "knex";
import { knex } from "knex";
import { v7 } from "uuid";

export const [useProvideQueryBuilderApi, _useQueryBuilderApi] = createInjectionState(
    (schema: MaybeRefOrGetter<MongoRaw | undefined>) => {
        const qb = shallowRef(knex({ client: "pg" }));
        const activeSchema = computed(() => toValue(schema));
        const importName = computed(() => activeSchema.value?.import_name ?? "");

        const columns = computed<Components.QueryBuilder.KnexColumn[]>(() => {
            if (activeSchema.value) {
                return QueryBuilderUtils.mongoSchemaToColumns(activeSchema.value.active_schema);
            }

            return [];
        });

        const columnNames = computed(() => columns.value.map((c) => c.name));

        function getColumn(name: string): Components.QueryBuilder.KnexColumn | undefined {
            return columns.value.find((c) => c.name === name);
        }

        function opsForCol(colName: string): Components.QueryBuilder.Operators.ConditionOperator[] {
            const col = getColumn(colName);
            if (col) {
                return QueryBuilderUtils.options.forColumn(col);
            }

            return ["=", "!=", "IS NULL", "IS NOT NULL"];
        }

        const selectedCols = useState<Components.QueryBuilder.ColumnSelection[]>(
            NuxtKeys.Components.QueryBuilder.SelectedColumns(activeSchema.value),
            () =>
                columnNames.value.map<Components.QueryBuilder.ColumnSelection>((col) => ({
                    id: v7(),
                    col,
                })),
        );
        const whereTree = useState<Components.QueryBuilder.Nodes.GroupNode>(
            NuxtKeys.Components.QueryBuilder.WhereTree(activeSchema.value),
            () => QueryBuilderUtils.tree.makeGroup("AND"),
        );
        const orderBy = useState<Components.QueryBuilder.OrderByState>(
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

        // ── Column actions ───────────────────────────────────────────────────────

        function addColumn() {
            selectedCols.value.push({ id: v7(), col: columnNames.value[0] ?? "" });
        }

        function removeColumn(id: string) {
            selectedCols.value = selectedCols.value.filter((c) => c.id !== id);
        }

        function selectAllColumns() {
            selectedCols.value = columnNames.value.map<Components.QueryBuilder.ColumnSelection>(
                (col) => ({
                    id: v7(),
                    col,
                }),
            );
        }

        function updateColumn(id: string, col: string | undefined) {
            const t = selectedCols.value.find((c) => c.id === id);
            if (!t || !col) {
                return;
            }

            t.col = col;
        }

        // ── Where actions ────────────────────────────────────────────────────────

        function resolveGroup(
            groupId: string | "root",
        ): Components.QueryBuilder.Nodes.GroupNode | null {
            if (groupId === "root") {
                return whereTree.value;
            }
            const node = QueryBuilderUtils.tree.findNode(whereTree.value, groupId);

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
            group.children.push(
                QueryBuilderUtils.tree.makeCondition(columnNames.value[0] ?? "", "AND"),
            );
        }

        function addGroupTo(groupId: string | "root") {
            const group = resolveGroup(groupId);
            if (!group) {
                return;
            }
            group.children.push(QueryBuilderUtils.tree.makeGroup("AND", "AND"));
        }

        function removeNode(nodeId: string) {
            QueryBuilderUtils.tree.findAndRemove(whereTree.value, nodeId);
        }

        function removeAllNodes() {
            whereTree.value.children.length = 0;
        }

        function updateCondition(
            nodeId: string,
            patch: Partial<
                Pick<Components.QueryBuilder.Nodes.ConditionNode, "col" | "op" | "val" | "conj">
            >,
        ) {
            const node = QueryBuilderUtils.tree.findNode(whereTree.value, nodeId);
            if (node?.type === "condition") {
                Object.assign(node, patch);
            }
        }

        function updateGroup(
            nodeId: string,
            patch: Partial<Pick<Components.QueryBuilder.Nodes.GroupNode, "logic" | "conj">>,
        ) {
            const node = QueryBuilderUtils.tree.findNode(whereTree.value, nodeId);
            if (node?.type === "group") {
                Object.assign(node, patch);
            }
        }

        function toggleConj(nodeId: string) {
            const node = QueryBuilderUtils.tree.findNode(whereTree.value, nodeId);
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
            whereTree.value = QueryBuilderUtils.tree.makeGroup("AND");
            orderBy.value = { col: "", dir: "ASC" };
            limit.value = 0;
        }

        // ── Outputs ──────────────────────────────────────────────────────────────

        const queryOutput = computed<Components.QueryBuilder.KnexOutput | null>(() => {
            if (!activeSchema.value || !importName.value) {
                return null;
            }

            const cols = selectedCols.value.length ? selectedCols.value.map((c) => c.col) : ["*"];

            const builder = qb.value(TableUtils.getTableName(importName.value)).select(cols);

            if (whereTree.value.children.length) {
                builder.where((sub) =>
                    QueryBuilderUtils.knex.applyGroup(
                        sub as unknown as Knex.QueryBuilder,
                        whereTree.value,
                    ),
                );
            }

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

        watch(
            [importName, columnNames],
            ([_, names]) => {
                reset();

                if (!names.length) {
                    return;
                }

                selectedCols.value = names.map<Components.QueryBuilder.ColumnSelection>((col) => ({
                    id: v7(),
                    col,
                }));
            },
            { immediate: true },
        );

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
            const value = payload?.toString() ?? QB_ORDER_NONE;
            qb.state.orderBy.value.col = value === QB_ORDER_NONE ? "" : value;
        }

        return {
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
    (schema: MaybeRefOrGetter<MongoRaw | undefined>) => {
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
