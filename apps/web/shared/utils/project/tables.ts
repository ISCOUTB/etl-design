import type { Dtype } from "#shared/utils/schemas/types";
import { Hash, ToggleLeft, Type } from "lucide-vue-next";

const typeIconMap: Record<Dtype, Components.LucideIconComponent> = {
    string: Type,
    integer: Hash,
    float: Hash,
    double: Hash,
    boolean: ToggleLeft,
};

const typeColorMap: Record<Dtype, string> = {
    string: "text-emerald-600 bg-emerald-500/10",
    integer: "text-blue-600 bg-blue-500/10",
    float: "text-blue-600 bg-blue-500/10",
    double: "text-blue-600 bg-blue-500/10",
    boolean: "text-amber-600 bg-amber-500/10",
};

export const TableUtils = {
    getTableName(importName: string): string {
        const parts = importName.split("__");
        if (parts.length > 1) {
            return parts.slice(1).join(" / ");
        }

        return importName;
    },
    getIcon(dtype: Dtype): Components.LucideIconComponent {
        return typeIconMap[dtype] ?? Type;
    },
    getColor(dtype: Dtype): string {
        return typeColorMap[dtype] ?? typeColorMap.string;
    },
};
