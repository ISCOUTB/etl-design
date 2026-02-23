import type { LucideIcon, LucideProps } from "lucide-vue-next";
import { RouteLocationRaw } from "vue-router";
import { FunctionalComponent } from "vue";

declare global {
    namespace Components {
        type LucideIconComponent = LucideIcon | FunctionalComponent<LucideProps>;

        type ColorModeOption = {
            value: "light" | "dark" | "system";
            icon: Components.LucideIconComponent;
            label: string;
        };

        namespace GenericDropdown {
            type Item = Prettify<
                {
                    label: string;
                    shortcut?: string[];
                    icon?: Components.LucideIconComponent;
                    disabled?: boolean | (() => boolean);
                    hidden?: boolean | (() => boolean);
                } & OneOf<
                    [
                        { to: () => RouteLocationRaw },
                        { action: () => void },
                        { sub: Components.GenericDropdown.Item[][] },
                    ]
                >
            >;
        }

        namespace Sidebar {
            interface Group {
                title?: string;
                items: Components.Sidebar.GroupItem[];
            }

            type GroupItem =
                | Components.Sidebar.GroupItemKind
                | Components.Sidebar.GroupCollapsibleKind
                | Components.Sidebar.GroupActionButtonKind;

            interface BaseItem {
                label: string;
                icon?: LucideIconComponent;
                hidden?: boolean | (() => boolean);
            }

            type GroupItemKind = (BaseItem & { kind: "item" }) &
                (
                    | {
                          actionKind: "navigation";
                          to: () => RouteLocationRaw;
                      }
                    | { actionKind: "function"; action: () => unknown }
                );

            interface GroupCollapsibleKind extends Components.Sidebar.BaseItem {
                kind: "collapsible";
                defaultActive?: boolean;
                collapsibleItems: Components.Sidebar.GroupCollapsibleKindItem[];
            }

            type GroupCollapsibleKindItem = Prettify<
                BaseItem & OneOf<[{ to: () => RouteLocationRaw }, { action: () => void }]>
            >;

            interface GroupActionButtonKind extends Components.Sidebar.BaseItem {
                kind: "action-button";
                dropdownItems: Components.GenericDropdown.Item[][];
            }
        }
    }
}
