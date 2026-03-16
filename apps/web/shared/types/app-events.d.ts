declare global {
    namespace AppEvents {
        interface BusEvent {
            key: string;
            payload: unknown;
        }

        type Events =
            | { key: "event:dummy"; payload: undefined }
            | { key: "event:schema:table-created"; payload: undefined };

        type EventKey = Events["key"];

        type HandlerPayload<
            Events extends AppEvents.BusEvent,
            EventKey extends Events["key"],
        > = Extract<Events, { key: EventKey }>["payload"];
    }
}

export {};
