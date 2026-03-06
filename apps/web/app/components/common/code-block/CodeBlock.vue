<script setup lang="ts">
    import type { HTMLAttributes } from "vue";
    import { Copy } from "lucide-vue-next";
    import { toast } from "vue-sonner";
    import { cn } from "~/lib/utils";

    interface Props {
        content: string | undefined;
        file?: string;
        copyable?: boolean;
        ext?: string;
        class?: HTMLAttributes["class"];
    }

    const props = withDefaults(defineProps<Props>(), {
        copyable: true,
    });
    const content = computed(() => JSON.stringify(props.content ?? {}, null, 4));

    const clipboard = useClipboard();

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
                        @click="clipboard.copy(content)"
                    >
                        <Copy />
                    </Button>
                </template>
            </div>
        </template>

        <div class="p-4">
            <pre class="overflow text-xs text-muted-foreground" v-text="content" />
        </div>
    </div>
</template>
