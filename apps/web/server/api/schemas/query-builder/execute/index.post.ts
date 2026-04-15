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

const ExtraParams = z
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

export default defineWrappedResponseHandler(async (event) => {
    const logger = Logger.getInstance();
    const session = await getServerSession(event);
    if (!session) {
        throw createError({ status: 401, statusMessage: ResponseCodesRecord.Server.UnAuthorized });
    }

    const { projectId, tree } = await UtilsRepository.readBody(event, Schema);

    logger.info(tree);

    const project = await ProjectRepository.get(session, projectId);
    if (!project.db_host || !project.db_port) {
        throw createError({
            status: 400,
            statusMessage: ResponseCodesRecord.Server.Project.MissingConnectionParams,
        });
    }

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

    const extraParams = ExtraParams.safeParse(project.db_params);
    if (!extraParams.success) {
        logger.warn(`could not parse params for project ${projectId}`);
        throw createError({
            status: 400,
            statusText: ResponseCodesRecord.Server.Project.InvalidParams,
        });
    }

    const client = knex({
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

    const rows = await builder;

    return {
        rows,
        meta: {
            count: rows.length,
            table: tree.table,
        },
    };
});
