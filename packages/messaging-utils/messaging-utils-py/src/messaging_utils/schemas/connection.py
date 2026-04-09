from typing import List, NotRequired, TypedDict


class QueueInfo(TypedDict):
    queue: str
    durable: bool
    routing_key: str
    queue_type: NotRequired[str]
    delivery_limit: NotRequired[int]
    message_ttl_ms: NotRequired[int]


class ExchangeInfo(TypedDict):
    exchange: str
    type: str
    durable: bool
    queues: List[QueueInfo]


class RoutingKey(TypedDict):
    routing_key: str


class ConnectionParams(TypedDict):
    host: str
    port: int
    virtual_host: str
    username: str
    password: str


class AllConnectionParams(ConnectionParams):
    exchange: ExchangeInfo
