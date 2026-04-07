declare global {
    namespace Breadcrumb {
        type Auto = ArrayType<ReturnType<typeof useBreadcrumbItems>["value"]>;

        interface PageMeta {
            kind?: "page" | "link";
            label?: string;
            options?: {
                parent?: Breadcrumb.PageMeta;
            };
            overrides?: {
                [K in keyof Omit<Breadcrumb.PageMeta, "overrides">]?: {
                    keypath: string;
                };
            };
        }

        type Child = Breadcrumb.Auto & { options: Breadcrumb.PageMeta["options"] };

        type GeneratedItem = { kind: "ellipsis" } | Breadcrumb.PageMeta | Breadcrumb.Auto;
    }
}

export {};
