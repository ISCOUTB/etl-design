<script setup lang="ts" generic="TContent">
    import type { HTMLAttributes } from "vue";
    import { Check, Copy } from "lucide-vue-next";
    import { toast } from "vue-sonner";
    import { cn } from "~/lib/utils";

    interface Props<T> {
        content: MaybeRefOrGetter<T | string | undefined>;
        file?: MaybeRefOrGetter<string | undefined>;
        copyable?: boolean;
        ext?: string;
        class?: HTMLAttributes["class"];
    }

    const props = withDefaults(defineProps<Props<TContent>>(), {
        copyable: true,
    });
    const content = computed(() => toValue(props.content));
    const file = computed(() => toValue(props.file));

    const parsedContent = computed(() => JSON.stringify(content.value ?? {}, null, 4));

    const clipboard = useClipboard();
    const animations = useClipboardAnimations();

    function handleCopy(event: MouseEvent) {
        clipboard.copy(parsedContent.value);
        animations.animateButtonClick(event);
    }

    onMounted(() => {
        whenever(clipboard.copied, () => toast.success($t("common.clipboard.copied")), {
            immediate: true,
        });
    });
</script>

<template>
    <div :class="cn('group overflow-hidden rounded-lg border bg-muted/50', props.class)">
        <template v-if="file || ext || copyable">
            <div class="flex items-center justify-between border-b bg-muted/80 px-4 py-2">
                <div class="flex items-center space-x-2">
                    <template v-if="file">
                        <span class="text-sm font-medium text-foreground">
                            <template v-if="$te(file)">
                                {{ $t(file) }}
                            </template>
                            <template v-else>{{ file }}</template>
                        </span>
                    </template>

                    <template v-if="ext">
                        <Badge variant="outline">
                            {{ ext }}
                        </Badge>
                    </template>
                </div>

                <template v-if="copyable">
                    <Button
                        variant="outline"
                        size="icon-sm"
                        class="opacity-0 group-hover:opacity-100 transition-opacity"
                        @click="handleCopy"
                    >
                        <Transition
                            :css="false"
                            mode="out-in"
                            @enter="animations.onIconEnter"
                            @leave="animations.onIconLeave"
                        >
                            <Check v-if="clipboard.copied.value" />
                            <Copy v-else />
                        </Transition>
                    </Button>
                </template>
            </div>
        </template>

        <div class="p-4">
            <pre class="overflow text-xs text-muted-foreground" v-text="parsedContent" />
        </div>
    </div>
</template>
