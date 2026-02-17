import type { UseWebSocketReturn } from "@vueuse/core";

declare module "#app" {
    interface NuxtApp {
        $socket: UseWebSocketReturn<WebSocket.Message>;
    }

    interface PageMeta {
        title: string;
    }
}

declare module "vue" {
    interface ComponentCustomProperties {
        $socket: UseWebSocketReturn<WebSocket.Message>;
    }
}
