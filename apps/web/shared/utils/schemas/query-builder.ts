import { z } from "zod";

export const DatabaseExtraParams = z
    .string()
    .nullable()
    .transform((str) => {
        try {
            if (str) {
                return JSON.parse(str);
            }

            return {};
        } catch {}
    })
    .pipe(z.record(z.string(), z.unknown()));

const LogicOperator = z.enum(["AND", "OR"]);

const ConditionOperator = z.enum([
    "=",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "LIKE",
    "ILIKE",
    "IN",
    "NOT IN",
    "IS NULL",
    "IS NOT NULL",
]);

const ConditionNode = z.object({
    id: z.coerce.string(),
    type: z.literal("condition"),
    col: z.coerce.string(),
    op: ConditionOperator,
    val: z.coerce.string(),
    conj: LogicOperator,
});

export const ColumnSelection = z.object({
    id: z.coerce.string(),
    col: z.coerce.string(),
});

export const GroupNode: z.ZodType<Components.QueryBuilder.Nodes.GroupNode> = z.lazy(() =>
    z.object({
        id: z.coerce.string(),
        type: z.literal("group"),
        logic: LogicOperator,
        children: z.array(z.union([ConditionNode, GroupNode])),
        conj: LogicOperator,
    }),
);

export const QueryNode = z.union([ConditionNode, GroupNode]);
