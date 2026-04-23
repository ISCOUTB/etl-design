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
    const { $logger } = useNuxtApp();
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

        const defaults = getDefaultErrorMessage(errorCode);
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

        $logger.warn(error);
        if (error instanceof FetchError && error.data) {
            const parsedError = ApiErrorSchema.safeParse(error.data);
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
