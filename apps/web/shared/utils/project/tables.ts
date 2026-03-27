import type { Dtype } from "#shared/utils/schemas/types";
import { cva } from "class-variance-authority";
import { Hash, ToggleLeft, Type } from "lucide-vue-next";

const typeIconMap: Record<Dtype, Components.LucideIconComponent> = {
    string: Type,
    integer: Hash,
    float: Hash,
    double: Hash,
    boolean: ToggleLeft,
};

const dtypeColorVariants = cva("text-foreground bg-muted", {
    variants: {
        dtype: {
            string: "text-emerald-600 bg-emerald-500/10",
            integer: "text-blue-600 bg-blue-500/10",
            float: "text-blue-600 bg-blue-500/10",
            double: "text-blue-600 bg-blue-500/10",
            boolean: "text-amber-600 bg-amber-500/10",
        },
    },
    defaultVariants: {
        dtype: "string",
    },
});

const propertiesColorVariants = cva("gap-1 text-[10px] border-500/50 bg-500/10", {
    variants: {
        type: {
            primary: "border-amber-500/50 bg-amber-500/10 text-amber-700",
            unique: "border-cyan-500/50 bg-cyan-500/10 text-cyan-700",
            optional: "text-muted-foreground bg-muted",
        },
    },
});

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
    getColor(dtype: Dtype | undefined): string {
        return dtypeColorVariants({ dtype });
    },
    getPropertiesColor(type: "primary" | "unique" | "optional") {
        return propertiesColorVariants({ type });
    },
};
