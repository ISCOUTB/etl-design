/* eslint-disable style/type-generic-spacing */

export default function <Events extends AppEvents.BusEvent = AppEvents.Events>() {
    function emit<K extends Events["key"]>(key: K, payload: AppEvents.HandlerPayload<Events, K>) {
        const bus = useEventBus(key);
        bus.emit(payload);
    }

    function on<K extends Events["key"]>(
        key: K,
        handler: (payload: AppEvents.HandlerPayload<Events, K>) => void,
    ) {
        const bus = useEventBus(key);
        bus.on(handler);
    }

    function once<K extends Events["key"]>(
        key: K,
        handler: (payload: AppEvents.HandlerPayload<Events, K>) => void,
    ) {
        const bus = useEventBus(key);
        bus.once(handler);
    }

    return {
        emit,
        on,
        once,
    };
}
