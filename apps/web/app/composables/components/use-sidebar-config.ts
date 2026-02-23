import { Boxes, FolderOpen, PlusSquare } from "lucide-vue-next";

export default function () {
    const SIDEBAR_CONFIG: Components.Sidebar.Group[] = [
        {
            items: [
                {
                    kind: "collapsible",
                    label: "projects.title",
                    defaultActive: true,
                    icon: FolderOpen,
                    collapsibleItems: [
                        {
                            label: "projects.create.title",
                            icon: PlusSquare,
                            to: () => "/projects/create",
                        },
                        {
                            label: "projects.view.title",
                            icon: Boxes,
                            to: () => "/",
                        },
                    ],
                },
            ],
        },
    ];

    const sidebarContent = computed(() => SIDEBAR_CONFIG);

    return {
        sidebarContent,
    };
}
