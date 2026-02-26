<script setup lang="ts">
    import type { Locale } from "#i18n";
    import type { ClassValue } from "class-variance-authority/types";
    import type { AcceptableValue, SelectContentProps } from "reka-ui";
    import { Languages } from "lucide-vue-next";
    import { toast } from "vue-sonner";
    import { cn } from "~/lib/utils";

    defineOptions({
        inheritAttrs: false,
    });

    const props = withDefaults(defineProps<Props>(), {
        behaviour: "change-locale",
        modelValue: undefined,
        contentProps: undefined,
    });

    const emit = defineEmits<{ "update:modelValue": [value: Locale] }>();

    interface Props {
        behaviour?: "change-locale" | "select";
        modelValue?: Locale;
        contentProps?: SelectContentProps;
    }

    const { locale, locales } = useI18n();

    const router = useRouter();
    const switchLocalePath = useSwitchLocalePath();

    function handleChange(locale: AcceptableValue) {
        const targetLocale = locale as Locale;

        if (props.behaviour === "change-locale") {
            const targetPath = switchLocalePath(targetLocale);
            router.push(targetPath);

            toast.success($t("settings.locale.changed_to", { locale: targetLocale }));

            return;
        }

        emit("update:modelValue", targetLocale);
    }

    const { getKbdKey } = useKbd();
    defineShortcuts(
        {
            meta_shift_l: {
                handler: () => {
                    const currentIdx = locales.value.findIndex((l) => l.code === locale.value);
                    const nextIdx = (currentIdx + 1) % locales.value.length;
                    const nextLocale = locales.value[nextIdx]?.code;

                    if (nextLocale) {
                        handleChange(nextLocale);
                    }
                },
            },
        },
        { layoutIndependent: true },
    );
</script>

<template>
    <Select :default-value="locale" :model-value="modelValue" @update:model-value="handleChange">
        <SelectTrigger :class="cn('h-10 w-32', $attrs.class as ClassValue)">
            <slot name="trigger">
                <Languages class="size-4" />
                <SelectValue />
            </slot>
        </SelectTrigger>
        <SelectContent class="w-44" v-bind="contentProps">
            <SelectGroup>
                <template v-for="_locale in locales" :key="_locale.code">
                    <SelectItem :value="_locale.code">
                        {{ _locale.name }}
                    </SelectItem>
                </template>
            </SelectGroup>
            <SelectSeparator />
            <div class="flex items-center justify-center select-none pointer-events-none">
                <KbdGroup>
                    <Kbd>{{ getKbdKey("meta") }}</Kbd>
                    <span>+</span>
                    <Kbd>{{ getKbdKey("shift") }}</Kbd>
                    <span>+</span>
                    <Kbd>{{ getKbdKey("l") }}</Kbd>
                </KbdGroup>
            </div>
        </SelectContent>
    </Select>
</template>
