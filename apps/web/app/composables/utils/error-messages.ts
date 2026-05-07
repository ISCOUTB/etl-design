import type { ExternalToast } from "vue-sonner";

interface ErrorCodeDefaults {
    title: string;
    description?: string;
    position?: ExternalToast["position"];
}

export function getDefaultErrorMessage(
    errorCode: ResponseCodes.Code | string | undefined,
): ErrorCodeDefaults {
    switch (errorCode) {
        case ResponseCodesRecord.Server.Auth.SignIn.InvalidCredentials: {
            return {
                title: "errors.auth.invalid_credentials.title",
            };
        }

        case ResponseCodesRecord.Server.Auth.SignIn.UserNotFound: {
            return {
                title: "errors.auth.user_not_found.title",
                description: "errors.auth.user_not_found.description",
            };
        }

        case ResponseCodesRecord.Server.BadPayload: {
            return {
                title: "errors.bad_payload.title",
                description: "errors.bad_payload.description",
            };
        }

        case ResponseCodesRecord.Server.UnAuthorized: {
            return {
                title: "errors.auth.unauthorized.title",
                description: "errors.auth.unauthorized.description",
            };
        }

        case ResponseCodesRecord.Server.UnAutenticated: {
            return {
                title: "errors.auth.unauthenticated.title",
                description: "errors.auth.unauthenticated.description",
            };
        }

        case ResponseCodesRecord.Server.Project.NotFound: {
            return {
                title: "errors.project.not_found.title",
                description: "errors.project.not_found.description",
            };
        }

        case ResponseCodesRecord.Server.Project.Schema.NoFileProvided: {
            return {
                title: "errors.project.file_not_provided.title",
            };
        }

        case ResponseCodesRecord.Server.Project.QueryBuilder.GenerateError: {
            return {
                title: "errors.project.query_builder.generate_error.title",
                description: "errors.project.query_builder.generate_error.description",
            };
        }

        case ResponseCodesRecord.Server.Project.QueryBuilder.InvalidColumns: {
            return {
                title: "errors.project.query_builder.invalid_columns.title",
                description: "errors.project.query_builder.invalid_columns.description",
            };
        }

        case ResponseCodesRecord.Server.Project.QueryBuilder.InvalidOrderBY: {
            return {
                title: "errors.project.query_builder.invalid_order_by.title",
                description: "errors.project.query_builder.invalid_order_by.description",
            };
        }

        case ResponseCodesRecord.Server.Project.QueryBuilder.ParseRowsError: {
            return {
                title: "errors.project.query_builder.parse_rows_error.title",
                description: "errors.project.query_builder.parse_rows_error.description",
            };
        }

        case ResponseCodesRecord.Server.Project.CouldNotConnect: {
            return {
                title: "errors.project.query_builder.could_not_connect.title",
                description: "errors.project.query_builder.could_not_connect.description",
            };
        }

        case ResponseCodesRecord.Server.Database.PsycopException: {
            return {
                title: "errors.database.psycop_exception.title",
                description: "errors.database.psycop_exception.description",
            };
        }

        default: {
            return {
                title: "errors.unknown.title",
                description: "errors.unknown.description",
            };
        }
    }
}
