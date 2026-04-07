<script setup lang="ts">
    import type { TooltipContentProps } from "reka-ui";
    import { Laptop, Moon, Sun } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    interface Props {
        contentProps?: TooltipContentProps;
    }

    defineProps<Props>();

    const button = useTemplateRef("button");
    const colorMode = useColorMode();
    const utils = useAnimationsUtils();

    const modes: Components.ColorModeOption[] = [
        {
            value: "light",
            icon: Sun,
            label: "settings.color_mode.light",
        },
        {
            value: "dark",
            icon: Moon,
            label: "settings.color_mode.dark",
        },
        {
            value: "system",
            icon: Laptop,
            label: "settings.color_mode.system",
        },
    ];

    const currentMode = computed(
        () => modes.find((mode) => mode.value === colorMode.preference) || modes[0]!,
    );

    function getNextMode(
        current: Components.ColorModeOption["value"],
    ): Components.ColorModeOption["value"] {
        const currentIndex = modes.findIndex((mode) => mode.value === current);
        const nextIndex = (currentIndex + 1) % modes.length;
        return modes[nextIndex]?.value ?? modes[0]!.value;
    }

    function updateTheme() {
        const nextMode = getNextMode(colorMode.preference as Components.ColorModeOption["value"]);

        colorMode.preference = nextMode;
        toast.success(
            $t("settings.color_mode.changed_to", {
                mode: nextMode.charAt(0).toUpperCase() + nextMode.slice(1),
            }),
        );
    }

    function updateColorMode() {
        if (!document.startViewTransition || utils.noAnimations.value) {
            updateTheme();
            return;
        }

        const buttonElement: HTMLElement | undefined = button.value?.$el || button.value;
        const rect = buttonElement?.getBoundingClientRect();

        if (rect) {
            const x = ((rect.left + rect.width / 2) / window.innerWidth) * 100;
            const y = ((rect.top + rect.height / 2) / window.innerHeight) * 100;

            document.documentElement.style.setProperty("--view-transition-x", `${x}%`);
            document.documentElement.style.setProperty("--view-transition-y", `${y}%`);
        }

        document.startViewTransition(() => {
            updateTheme();
        });
    }

    const { getKbdKey } = useKbd();
    defineShortcuts(
        {
            meta_k: {
                handler: () => updateColorMode(),
            },
        },
        { layoutIndependent: true },
    );
</script>

<template>
    <ClientOnly>
        <TooltipProvider>
            <Tooltip :delay-duration="1000">
                <TooltipTrigger as-child>
                    <Button ref="button" variant="outline" size="icon" @click="updateColorMode">
                        <component :is="currentMode.icon" class="size-4" />
                        <span class="sr-only">{{ $t(currentMode.label) }}</span>
                    </Button>
                </TooltipTrigger>
                <TooltipContent v-bind="contentProps">
                    <p class="line-clamp-2 flex items-center gap-2">
                        {{ $t(currentMode.label) }}
                        <KbdGroup>
                            <Kbd>{{ getKbdKey("meta") }}</Kbd>
                            <span>+</span>
                            <Kbd>{{ getKbdKey("k") }}</Kbd>
                        </KbdGroup>
                    </p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>

        <template #fallback>
            <div class="size-9 rounded-md bg-muted animate-pulse inline-block" />
        </template>
    </ClientOnly>
</template>

<style lang="css">
    ::view-transition-old(root) {
        animation-delay: 500ms;
    }

    ::view-transition-new(root) {
        animation: circle-in 1250ms;
    }

    @keyframes circle-in {
        from {
            clip-path: circle(0% at var(--view-transition-x, 50%) var(--view-transition-y, 0%));
        }
        to {
            clip-path: circle(200% at var(--view-transition-x, 50%) var(--view-transition-y, 0%));
        }
    }

    @media (prefers-reduced-motion: reduce) {
        ::view-transition-old(root),
        ::view-transition-new(root) {
            animation: none;
        }
    }
</style>
