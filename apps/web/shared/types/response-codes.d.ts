/* eslint-disable style/indent */
import type { ResponseCodesRecord } from "#shared/utils/response-codes";

declare global {
    namespace ResponseCodes {
        type ExtractCodes<T> = T extends string
            ? T
            : T extends object
              ? ResponseCodes.ExtractCodes<T[keyof T]>
              : never;

        type Code = ResponseCodes.ExtractCodes<typeof ResponseCodesRecord>;
    }
}
