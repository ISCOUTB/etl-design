import type { Dtype } from "#shared/utils/schemas/types";
import { Hash, ToggleLeft, Type } from "lucide-vue-next";

const typeIconMap: Record<Dtype, Components.LucideIconComponent> = {
    string: Type,
    integer: Hash,
    float: Hash,
    double: Hash,
    boolean: ToggleLeft,
};

export const TableUtils = {
    getTableName(importName: string): string {
        const separator = "__";
        const firstIndex = importName.indexOf(separator);

        if (firstIndex !== -1) {
            return importName.substring(firstIndex + separator.length);
        }

        return importName;
    },
    getIcon(dtype: Dtype): Components.LucideIconComponent {
        return typeIconMap[dtype] ?? Type;
    },
};
