import { useClipboard } from "@vueuse/core";
import { toast } from "vue-sonner";

export default function () {
    const { t } = useI18n();
    const clipboard = useClipboard();
    const animations = useClipboardAnimations();

    function handleCopy(content: string, $event: MouseEvent | undefined) {
        clipboard.copy(content);
        if ($event) {
            animations.animateButtonClick($event);
        }
    }

    if (getCurrentInstance()) {
        onMounted(() => {
            whenever(clipboard.copied, () => toast.success(t("common.clipboard.copied")), {
                immediate: true,
            });
        });
    }

    return { ...clipboard, animations, handleCopy };
}
