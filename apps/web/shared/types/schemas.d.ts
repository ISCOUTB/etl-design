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
            interface UploadedFile {
                name: string;
                nameWithoutExt: string;
                size: string;
                type: string;
                file: File;
                blob: Blob;
            }
        }
    }
}

export {};
