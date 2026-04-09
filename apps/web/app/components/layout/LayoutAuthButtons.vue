<script setup lang="ts">
    import { LogIn, UserRound, UserRoundPlus } from "lucide-vue-next";
    import { useSidebar } from "@/components/ui/sidebar";

    const { isMobile } = useSidebar();
    const { $localeRoute } = useNuxtApp();
    const dropdownItems = computed<Components.GenericDropdown.Item[][]>(() => [
        [
            {
                label: "auth.sign_up.title",
                icon: UserRoundPlus,
                to: () => $localeRoute({ name: "auth-sign-up" }),
            },
            {
                label: "auth.sign_in.title",
                icon: LogIn,
                to: () => $localeRoute({ name: "auth-sign-in" }),
            },
        ],
    ]);
</script>

<template>
    <ClientOnly>
        <template v-if="isMobile">
            <DropdownMenuRoot
                :items="dropdownItems"
                :root-props="{ modal: false }"
                :content-props="{ align: 'end' }"
            >
                <template #trigger>
                    <Button variant="secondary" size="icon" class="cursor-pointer">
                        <UserRound />
                    </Button>
                </template>
            </DropdownMenuRoot>
        </template>
        <template v-else>
            <div class="space-x-2">
                <Button variant="secondary" as-child>
                    <NuxtLink :to="$localeRoute({ name: 'auth-sign-up' })">
                        {{ $t("auth.sign_up.title") }}
                    </NuxtLink>
                </Button>
                <Button variant="outline">
                    <NuxtLink :to="$localeRoute({ name: 'auth-sign-in' })">
                        {{ $t("auth.sign_in.title") }}
                    </NuxtLink>
                </Button>
            </div>
        </template>

        <template #fallback>
            <div class="size-9 rounded-md bg-muted animate-pulse inline-block" />
        </template>
    </ClientOnly>
</template>
