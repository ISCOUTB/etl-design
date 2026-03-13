import type { ExternalToast } from "vue-sonner";
import { ResponseCodesRecord } from "#shared/utils/response-codes";
import { ApiErrorSchema } from "#shared/utils/schemas/api";
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
                    title: t("errors.auth.invalid_credentials.title"),
                };
            }

            case ResponseCodesRecord.Server.Auth.SignIn.UserNotFound: {
                return {
                    title: t("errors.auth.user_not_found.title"),
                    description: t("errors.auth.user_not_found.description"),
                };
            }

            case ResponseCodesRecord.Server.BadPayload: {
                return {
                    title: t("errors.bad_payload.title"),
                    description: t("errors.bad_payload.description"),
                };
            }

            case ResponseCodesRecord.Server.UnAuthorized: {
                return {
                    title: t("errors.auth.unauthorized.title"),
                    description: t("errors.auth.unauthorized.description"),
                };
            }

            case ResponseCodesRecord.Server.UnAutenticated: {
                return {
                    title: t("errors.auth.unauthenticated.title"),
                    description: t("errors.auth.unauthenticated.description"),
                };
            }

            case ResponseCodesRecord.Server.Project.NotFound: {
                return {
                    title: $t("errors.project.not_found.title"),
                    description: $t("errors.project.not_found.description"),
                };
            }

            case ResponseCodesRecord.Server.Project.Schema.NoFileProvided: {
                return {
                    title: $t("errors.project.file_not_provided.title"),
                };
            }

            default: {
                return {
                    title: t("errors.unknown.title"),
                    description: t("errors.unknown.description"),
                };
            }
        }
    }

    function show(notification: ToastNotification) {
        const { title, description, ...rest } = notification;

        toast.error(resolveI18nText(title) ?? title, {
            description: resolveI18nText(description) ?? description,
            ...rest,
        });
    }

    function handle(payload: unknown, props?: Props) {
        const { handler, ...options } = props ?? {};

        if (typeof payload === "object") {
            const error = ApiErrorSchema.safeParse(payload);
            const errorType = error.data?.error;
            const defaults = getDefaults(errorType);

            const merged: ToastNotification = {
                ...defaults,
                ...(errorType ? handler?.[errorType as ResponseCodes.Code] : {}),
                ...options,
            };

            show(merged);

            return;
        }

        const error = String(payload);
        const defaults = getDefaults(error);
        const merged: ToastNotification = {
            ...defaults,
            ...handler?.[error as ResponseCodes.Code],
            ...options,
        };

        show(merged);
    }

    return {
        handle,
    };
}
