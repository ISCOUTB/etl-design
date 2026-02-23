<script setup lang="ts">
    import type { DropdownMenuContentProps } from "reka-ui";
    import { ChevronsUpDown } from "lucide-vue-next";
    import { toast } from "vue-sonner";
    import { useSidebar } from "@/components/ui/sidebar";

    const { $localePath } = useNuxtApp();
    const auth = useAuth();

    const { isMobile } = useSidebar();
    const dropdownSide = computed<DropdownMenuContentProps["side"]>(() => {
        if (isMobile.value) {
            return "bottom";
        }

        return "right";
    });

    function extractAvatarFallback(name: string | undefined): string {
        if (!name) {
            return "User";
        }

        return name
            .split(" ")
            .map((slice) => slice.charAt(0))
            .slice(0, 2)
            .join("");
    }

    const avatarFallback = computed(() => extractAvatarFallback(auth.data.value?.user.name));
    const items: Components.GenericDropdown.Item[][] = [
        [
            {
                label: "auth.sign_out.title",
                action: () => {
                    auth.signOut({
                        callbackUrl: $localePath({
                            path: "/auth/sign-in",
                            query: { email: auth.data.value?.user.email },
                        }),
                    });

                    toast.success($t("auth.events.user_signout.title"));
                },
            },
        ],
    ];
</script>

<template>
    <SidebarMenu>
        <SidebarMenuItem>
            <DropdownMenuRoot
                :items="items"
                :content-props="{
                    class: 'w-[--reka-dropdown-menu-trigger-width] min-w-56 rounded-lg',
                    side: dropdownSide,
                    align: 'end',
                    sideOffset: 4,
                }"
            >
                <template #trigger>
                    <SidebarMenuButton
                        size="lg"
                        class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                    >
                        <Avatar class="h-8 w-8 rounded-lg">
                            <AvatarFallback class="rounded-lg">
                                {{ avatarFallback }}
                            </AvatarFallback>
                        </Avatar>
                        <div class="grid flex-1 text-left text-sm leading-tight">
                            <span class="truncate font-medium">{{
                                auth.data.value?.user.name
                            }}</span>
                            <span class="truncate text-xs">{{ auth.data.value?.user.email }}</span>
                        </div>
                        <ChevronsUpDown class="ml-auto size-4" />
                    </SidebarMenuButton>
                </template>

                <template #dropdown-header>
                    <DropdownMenuLabel class="p-0 font-normal">
                        <div class="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                            <Avatar class="h-8 w-8 rounded-lg">
                                <AvatarFallback class="rounded-lg">
                                    {{ avatarFallback }}
                                </AvatarFallback>
                            </Avatar>
                            <div class="grid flex-1 text-left text-sm leading-tight">
                                <span class="truncate font-semibold">{{
                                    auth.data.value?.user.name
                                }}</span>
                                <span class="truncate text-xs">{{
                                    auth.data.value?.user.email
                                }}</span>
                            </div>
                        </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                </template>
            </DropdownMenuRoot>
        </SidebarMenuItem>
    </SidebarMenu>
</template>
