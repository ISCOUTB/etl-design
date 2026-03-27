/* eslint-disable style/indent-binary-ops */
/* eslint-disable style/indent */
declare global {
    namespace AppEvents {
        interface BusEvent {
            key: string;
            payload: unknown;
        }

        type Events =
            | { key: "event:schema:table-created"; payload: undefined }
            | {
                  key: "event:projects:change-tab";
                  payload: { value: string };
              }
            | {
                  key: "event:projects:table:change-view";
                  payload: { value: "overview" | "view" };
              }
            | {
                  key: "event:projects:table:set-selected-schema";
                  payload: { schema: MongoRaw | undefined };
              };

        type EventKey = Events["key"];

        type HandlerPayload<
            Events extends AppEvents.BusEvent,
            EventKey extends Events["key"],
        > = Extract<Events, { key: EventKey }>["payload"];
    }
}

export {};
