/* eslint-disable style/indent */
import type { UseWebSocketReturn } from "@vueuse/core";
import "vue-router";

// source: @sidebase/nuxt-auth/dist/runtime/middleware/sidebase-auth.d.ts
type AuthMiddlewareMeta =
    | boolean
    | {
          /**
           * Whether to allow only unauthenticated users to access this page.
           *
           * Authenticated users will be redirected to `/` or the route defined in `navigateAuthenticatedTo`
           */
          unauthenticatedOnly: boolean;
          /**
           * Where to redirect authenticated users if `unauthenticatedOnly` is set to true
           *
           * @default undefined
           */
          navigateAuthenticatedTo?: string;
          /**
           * Where to redirect unauthenticated users if this page is protected
           *
           * @default undefined
           */
          navigateUnauthenticatedTo?: string;
      };

declare module "#app" {
    interface NuxtApp {
        $socket: UseWebSocketReturn<WebSocket.Message>;
    }

    interface PageMeta {
        title: string;
        auth?: AuthMiddlewareMeta;
    }
}

declare module "vue" {
    interface ComponentCustomProperties {
        $socket: UseWebSocketReturn<WebSocket.Message>;
    }
}

declare module "vue-router" {
    interface RouteMeta {
        auth?: AuthMiddlewareMeta;
    }
}
