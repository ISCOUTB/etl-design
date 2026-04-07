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

        type ComponentLoader<C extends Component> = () => Promise<{
            default: C;
        }>;

        type ComponentProps<C extends Component> = C extends new (...args: any) => any
            ? Omit<InstanceType<C>["$props"], keyof VNodeProps | keyof AllowedComponentProps>
            : never;

        namespace GenericDropdown {
            interface Item<TContext = unknown> {
                label: string;
                shortcut?: string[];
                icon?: Components.LucideIconComponent;
                disabled?: boolean | ((ctx?: TContext) => boolean);
                hidden?: boolean | (() => boolean);
                to?: (ctx?: TContext) => RouteLocationRaw;
                action?: (ctx?: TContext) => void;
                sub?: Components.GenericDropdown.Item<TContext>[][];
            }
        }

        namespace Modal {
            type Kind = "sheet" | "dialog" | "alert-dialog" | "drawer";

            interface State {
                currentModalKey: string | undefined;
                currentKind: Components.Modal.Kind;
                open: boolean;
                componentProps: object;
            }

            interface Args<C extends Component> {
                loader: Components.ComponentLoader<C>;
                kind?: Components.Modal.Kind;
                props?: Components.ComponentProps<C>;
                key: string;
            }
        }

        namespace TabsManager {
            interface TabMeta {
                label: string;
                value: string;
                icon?: Components.LucideIconComponent;
                atomic?: boolean;
            }

            interface TabDefinition<C extends Component> {
                meta: Components.TabsManager.TabMeta;
                component: Components.Modal.ComponentLoader<C>;
                props?: Components.Modal.ComponentProps<C>;
            }

            interface LoadedComponent<C extends Component> {
                meta: Components.TabsManager.TabMeta;
                component: C;
                props?: Components.Modal.ComponentProps<C>;
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
                menuAction?: () => unknown;
                collapsibleItems: Components.Sidebar.GroupCollapsibleKindItem[];
            }

            type GroupCollapsibleKindItem = Prettify<
                BaseItem & OneOf<[{ to: () => RouteLocationRaw }, { action: () => void }]>
            >;

            interface GroupActionButtonKind extends Components.Sidebar.BaseItem {
                kind: "action-button";
                menuAction?: () => unknown;
                dropdownItems: Components.GenericDropdown.Item[][];
            }
        }
    }
}
