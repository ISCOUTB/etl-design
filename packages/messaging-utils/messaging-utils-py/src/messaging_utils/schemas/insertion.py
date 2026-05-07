from typing import Dict, Literal, Optional, TypedDict

from messaging_utils.schemas.common import Metadata

InsertionTasks = Literal["sample_insertion", "unknown"]


class InsertionMessage(TypedDict):
    """
    id (str): Unique identifier for the message.
    task (InsertionTasks): The type of insertion task to perform.
    file_data (str): The data of the file to be inserted, encoded as hex.
    project_id (str): The name of the table or collection to insert into.
    table_name (str): The name of the table or collection to insert into.
    scheme (str): The database scheme where the table is located.
    metadata (Metadata): Metadata about the file, including filename, content type, and size.
    date (str): The date when the message was created, in ISO format.
    extra (Dict[str, str]): A dictionary of additional key-value pairs for extensibility.
    overwrite (bool): A flag indicating whether to overwrite to existing data (True) or append (False).
    db_uri (str): The URI for connecting to the database where the data should be inserted.
    idempotency_key (Optional[str]): A unique key for ensuring idempotent processing of the insertion request.
    traceparent (Optional[str]): W3C Trace Context traceparent header for distributed tracing.
    tracestate (Optional[str]): W3C Trace Context tracestate header for distributed tracing.
    baggage (Optional[str]): Baggage header for distributed context propagation.
    """

    id: str
    task: InsertionTasks
    file_data: str
    project_id: str
    table_name: str
    scheme: Optional[str]
    metadata: Metadata
    date: str
    extra: Dict[str, str]
    overwrite: bool
    db_uri: str
    idempotency_key: Optional[str]
    # W3C Trace Context headers for distributed tracing
    traceparent: Optional[str]
    tracestate: Optional[str]
    baggage: Optional[str]
