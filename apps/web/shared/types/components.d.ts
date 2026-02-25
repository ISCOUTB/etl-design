import type { LucideIcon, LucideProps } from "lucide-vue-next";
import { RouteLocationRaw } from "vue-router";
import { FunctionalComponent, AllowedComponentProps, VNodeProps } from "vue";

declare global {
    namespace Components {
        type LucideIconComponent = LucideIcon | FunctionalComponent<LucideProps>;

        type ColorModeOption = {
            value: "light" | "dark" | "system";
            icon: Components.LucideIconComponent;
            label: string;
        };

        namespace GenericDropdown {
            interface Item<TContext = unknown> {
                label: string;
                shortcut?: string[];
                icon?: Components.LucideIconComponent;
                disabled?: boolean | (() => boolean);
                hidden?: boolean | (() => boolean);
                to?: (ctx?: TContext) => RouteLocationRaw;
                action?: (ctx?: TContext) => void;
                sub?: Components.GenericDropdown.Item<TContext>[][];
            }
        }

        namespace Modal {
            type ComponentLoader<C extends Component> = () => Promise<{
                default: C;
            }>;

            type ComponentProps<C extends Component> = C extends new (...args: any) => any
                ? Omit<InstanceType<C>["$props"], keyof VNodeProps | keyof AllowedComponentProps>
                : never;

            interface Args<C extends Component> {
                loader: ComponentLoader<C>;
                props?: ComponentProps<C>;
                key: string;
            }
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
