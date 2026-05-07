import { Boxes, FolderOpen, PlusSquare, User } from "lucide-vue-next";

export default function () {
    const { $localeRoute } = useNuxtApp();
    const auth = useAuth();

    const SIDEBAR_CONFIG: Components.Sidebar.Group[] = [
        {
            items: [
                {
                    kind: "collapsible",
                    label: "projects.title",
                    defaultActive: true,
                    icon: FolderOpen,
                    menuAction: () => {
                        navigateTo($localeRoute({ name: "projects" }));
                    },
                    collapsibleItems: [
                        {
                            label: "projects.create.title",
                            icon: PlusSquare,
                            to: () => $localeRoute({ name: "projects-create" }),
                        },
                        {
                            label: "projects.view.title",
                            icon: Boxes,
                            to: () => $localeRoute({ name: "projects" }),
                        },
                    ],
                },
                {
                    kind: "item",
                    label: "Users",
                    icon: User,
                    actionKind: "navigation",
                    hidden: () => auth.data.value?.user.role !== "sudo",
                    to: () => $localeRoute({ name: "admin-users" }),
                },
            ],
        },
    ];

    const sidebarContent = computed(() => SIDEBAR_CONFIG);

    return {
        sidebarContent,
    };
}
