import { Info, Settings } from "lucide-vue-next";

export default function () {
    const manager = new TabsManager([
        {
            meta: {
                label: "projects.id.sections.general_information.tab",
                value: "section:general-information",
                icon: Info,
            },
            component: () => import("@/components/project/ProjectGeneralInformation.vue"),
        },
        {
            meta: {
                label: "projects.id.sections.settings.tab",
                value: "section:settings",
                icon: Settings,
            },
            component: () => import("@/components/project/ProjectSettings.vue"),
        },
    ]);

    return manager;
}
