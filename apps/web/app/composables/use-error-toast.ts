/**
 * Refactor this shit
 * Du not know how could I write this messy code
 *
 */

import type { ExternalToast } from "vue-sonner";
import { ResponseCodesRecord } from "#shared/utils/response-codes";
import { ApiErrorSchema } from "#shared/utils/schemas/api";
import { FetchError } from "ofetch";
import { toast } from "vue-sonner";

interface ErrorCodeDefaults {
    title: string;
    description?: string;
    position?: ExternalToast["position"];
}

type ToastNotification = ErrorCodeDefaults & ExternalToast;

type ServerResponseNotification = {
    [K in ResponseCodes.Code]?: Partial<ToastNotification>;
};

type Props = Partial<ToastNotification> & {
    handler?: ServerResponseNotification;
};

export default function () {
    const { t, te } = useI18n();

    function resolveI18nText<T>(value?: T) {
        if (!value) {
            return value;
        }

        if (typeof value !== "string") {
            return value;
        }

        if (te(value)) {
            return t(value);
        }

        return value;
    }

    function getDefaults(errorCode: ResponseCodes.Code | string | undefined): ErrorCodeDefaults {
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

            default: {
                return {
                    title: "errors.unknown.title",
                    description: "errors.unknown.description",
                };
            }
        }
    }

    function show(notification: ToastNotification) {
        const title = resolveI18nText(notification.title) || t("errors.unknown.title");
        const description = resolveI18nText(notification.description);

        // eslint-disable-next-line sonarjs/no-unused-vars
        const { title: _, description: __, ...options } = notification;

        toast.error(title || "errors.unknown.title", {
            ...options,
            description,
        });
    }

    function handle(payload: unknown, props?: Props): ToastNotification {
        const { handler, ...rest } = props ?? {};

        const options = Object.fromEntries(
            Object.entries(rest).filter(([_, v]) => v !== undefined),
        );

        const errorCode =
            payload && typeof payload === "object"
                ? ApiErrorSchema.safeParse(payload).data?.error
                : String(payload);

        const defaults = getDefaults(errorCode);
        const merged: ToastNotification = {
            ...defaults,
            ...(errorCode ? handler?.[errorCode as ResponseCodes.Code] : {}),
            ...options,
        };

        show(merged);

        return merged;
    }

    function handleServer(error: unknown) {
        if (!error) {
            return;
        }

        console.warn(error);
        if (error instanceof FetchError && error.data) {
            const parsedError = ApiErrorSchema.safeParse(error.data);
            console.warn(parsedError);
            if (!parsedError.success) {
                handle(ResponseCodesRecord.Server.UnknownError);

                return;
            }

            handle(parsedError.data.error);
        }
    }

    return {
        handle,
        handleServer,
    };
}
