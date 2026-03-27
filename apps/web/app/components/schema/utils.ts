import { cva } from "class-variance-authority";

export const dtypeColorVariants = cva("text-foreground bg-muted", {
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

export const propertiesColorVariants = cva("gap-1 text-[10px] border-500/50 bg-500/10", {
    variants: {
        type: {
            primary: "border-amber-500/50 bg-amber-500/10 text-amber-700",
            unique: "border-cyan-500/50 bg-cyan-500/10 text-cyan-700",
            optional: "text-muted-foreground bg-muted",
        },
    },
});
