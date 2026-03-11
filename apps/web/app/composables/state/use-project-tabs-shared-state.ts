interface UploadedFile {
    name: string;
    size: string;
    type: string;
    blob: Blob;
}

export default function () {
    const { t } = useI18n();

    const route = useRoute();
    const uploadedFile = useState<UploadedFile | undefined>(
        NuxtKeys.Projects.UploadFile(route.path),
        () => undefined,
    );

    const Section = computed<Tabs.Project.ProjectSections>(() => ({
        General: t("projects.id.sections.general_information.tab"),
        Schema: t("projects.id.sections.schema.tab"),
        Settings: t("projects.id.sections.settings.tab"),
        File: t("projects.id.sections.file.tab"),
    }));

    const tab = useRouteQuery<string>("tab", Section.value.General, {
        mode: "replace",
        transform: (value) => {
            const sections = Object.values(Section.value);
            const found = sections.find((section) => section === value);
            if (found) {
                return found;
            }

            return Section.value.General;
        },
    });

    return {
        uploadedFile,
        Section,
        tab,
    };
}
