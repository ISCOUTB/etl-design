import type { ResponseProject } from "#shared/utils/schemas/types";
import { getServerSession } from "#auth";
import knex from "knex";
import { z } from "zod";

const Schema = z.object({
    projectId: z.string(),
    tree: z.object({
        table: z.string(),
        select: z.array(z.string()),
        where: GroupNode,
        orderBy: z
            .object({
                col: z.string(),
                dir: z.enum(["ASC", "DESC"]),
            })
            .nullable(),
        limit: z.number().optional(),
    }),
});

function resolveClient(project: ResponseProject): knex.Knex {
    const logger = Logger.getInstance();

    if (project.db_host && project.db_port) {
        const extraParams = DatabaseExtraParams.safeParse(project.db_params);
        if (!extraParams.success) {
            logger.warn(`could not parse params for project ${project.id}`);
            throw createError({
                status: 400,
                statusText: ResponseCodesRecord.Server.Project.InvalidParams,
            });
        }

        return knex({
            client: "pg",
            connection: {
                host: project.db_host,
                port: project.db_port,
                user: project.db_user ?? undefined,
                password: project.db_password ?? undefined,
                database: project.db_name ?? undefined,
                ...extraParams.data,
            },
        });
    }

    const { database } = useRuntimeConfig();

    return knex({
        client: "pg",
        connection: {
            host: database.default.HOST,
            port: Number(database.default.PORT),
            user: database.default.USER,
            password: database.default.PASSWORD,
            database: database.default.DB,
        },
    });
}

export default defineWrappedResponseHandler(async (event) => {
    const logger = Logger.getInstance();
    const session = await getServerSession(event);
    if (!session) {
        throw createError({ status: 401, statusMessage: ResponseCodesRecord.Server.UnAuthorized });
    }

    const { projectId, tree } = await UtilsRepository.readBody(event, Schema);

    logger.info(tree);

    const project = await ProjectRepository.get(session, projectId);

    const table = await ProjectRepository.getTable(session, projectId, tree.table);
    const columns = QueryBuilderUtils.mongoSchemaToColumns(table.active_schema);
    const columnNames = columns.map((column) => column.name);

    const invalid = tree.select.filter((column) => column !== "*" && !columnNames.includes(column));
    if (invalid.length) {
        throw createError({
            status: 400,
            statusText: ResponseCodesRecord.Server.Project.QueryBuilder.InvalidColumns,
        });
    }

    if (tree.orderBy?.col && !columnNames.includes(tree.orderBy.col)) {
        throw createError({
            status: 400,
            statusText: ResponseCodesRecord.Server.Project.QueryBuilder.InvalidOrderBY,
        });
    }

    QueryBuilderUtils.validate.groupNode(columns, tree.where);

    const client = resolveClient(project);

    try {
        client.raw("SELECT 1");
    } catch {
        throw createError({
            status: 400,
            statusText: ResponseCodesRecord.Server.Project.CouldNotConnect,
        });
    }

    const builder = client(
        QueryBuilderUtils.standardize.normalize(TableUtils.getTableName(tree.table)),
    ).select(
        tree.select.map((column) => {
            if (column === "*") {
                return column;
            }

            return QueryBuilderUtils.standardize.normalize(column);
        }),
    );

    if (tree.where.children.length > 0) {
        builder.where((sub) =>
            QueryBuilderUtils.knex.applyGroup(
                sub,
                QueryBuilderUtils.standardize.where(
                    tree.where,
                    QueryBuilderUtils.standardize.normalize,
                ),
            ),
        );
    }

    if (tree.orderBy?.col) {
        builder.orderBy(
            QueryBuilderUtils.standardize.normalize(tree.orderBy.col),
            tree.orderBy.dir,
        );
    }

    if (typeof tree.limit === "number" && tree.limit > 0) {
        builder.limit(tree.limit);
    }

    const parsedRows = z.array(z.record(z.string(), z.unknown())).safeParse(await builder);
    if (!parsedRows.success) {
        throw createError({
            status: 500,
            statusText: ResponseCodesRecord.Server.Project.QueryBuilder.ParseRowsError,
        });
    }

    return {
        rows: parsedRows.data,
        meta: {
            count: parsedRows.data.length,
            table: tree.table,
        },
    };
});
