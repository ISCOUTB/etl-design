import type { LucideIcon, LucideProps } from "lucide-vue-next";

declare global {
    namespace Components {
        type LucideIconComponent = LucideIcon | FunctionalComponent<LucideProps>;

        type ColorModeOption = {
            value: "light" | "dark" | "system";
            icon: LucideIconComponent;
            label: string;
        };
    }
}
