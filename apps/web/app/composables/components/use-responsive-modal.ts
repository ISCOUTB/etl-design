import { useSidebar } from "~/components/ui/sidebar";

export default function () {
    const { isMobile } = useSidebar();

    function resolve(desktop: Components.Modal.Kind, mobile: Components.Modal.Kind) {
        if (isMobile.value) {
            return mobile;
        }

        return desktop;
    }

    return {
        resolve,
    };
}
