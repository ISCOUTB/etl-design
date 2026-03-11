declare global {
    namespace Schemas {
        namespace Project {
            interface ProjectInformation {
                label: string;
                value: string | undefined | null;
                fallbackValue: string;
                icon?: Components.LucideIconComponent;
                warning?: boolean;
                tooltip?: string;
            }
        }

        namespace Schema {
            type DataType = "text" | "integer" | "float" | "double" | "boolean";
        }
    }
}

export {};
