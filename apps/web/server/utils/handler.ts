import type { EventHandler, EventHandlerRequest } from "h3";
import { CachedEventHandlerOptions } from "nitropack";

export const defineWrappedResponseHandler = <T extends EventHandlerRequest, D>(
    handler: EventHandler<T, D>,
): EventHandler<T, D> =>
    defineEventHandler<T>(async (event) => {
        const logger = Logger.getInstance();

        try {
            const response = await handler(event);
            return response;
        } catch (error) {
            logger.error(error);

            if (error instanceof H3Error) {
                throw createError({ ...error });
            }

            throw createError({
                statusCode: 500,
                statusMessage: ResponseCodesRecord.Server.UnknownError,
            });
        }
    });

export function defineWrappedCachedResponseHandler<T extends EventHandlerRequest, D>(
    handler: EventHandler<T, D>,
    options?: CachedEventHandlerOptions,
): EventHandler<T, D> {
    return defineCachedEventHandler<T>(async (event) => {
        const logger = Logger.getInstance();

        try {
            const response = await handler(event);
            return response;
        } catch (error) {
            logger.error(error);

            if (error instanceof H3Error) {
                throw createError(error);
            }

            throw createError({
                statusCode: 500,
                statusMessage: ResponseCodesRecord.Server.UnknownError,
            });
        }
    }, options);
}
