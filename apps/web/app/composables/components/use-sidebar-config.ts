import { Boxes, FolderOpen, PlusSquare } from "lucide-vue-next";

export default function () {
    const { $localeRoute } = useNuxtApp();

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
            ],
        },
    ];

    const sidebarContent = computed(() => SIDEBAR_CONFIG);

    return {
        sidebarContent,
    };
}
