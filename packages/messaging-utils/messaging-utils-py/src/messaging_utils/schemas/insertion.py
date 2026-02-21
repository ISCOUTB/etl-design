from typing import Dict, Literal, TypedDict

from messaging_utils.schemas.common import Metadata

InsertionTasks = Literal["sample_insertion", "unknown"]


class InsertionMessage(TypedDict):
    """
    id (str): Unique identifier for the message.
    task (InsertionTasks): The type of insertion task to perform.
    file_data (str): The data of the file to be inserted, encoded as hex.
    project_id (str): The name of the table or collection to insert into.
    metadata (Metadata): Metadata about the file, including filename, content type, and size.
    date (str): The date when the message was created, in ISO format.
    extra (Dict[str, str]): A dictionary of additional key-value pairs for extensibility.
    overwrite (bool): A flag indicating whether to overwrite to existing data (True) or append (False).
    db_uri (str): The URI for connecting to the database where the data should be inserted.
    """

    id: str
    task: InsertionTasks
    file_data: str
    project_id: str
    metadata: Metadata
    date: str
    extra: Dict[str, str]
    overwrite: bool
    db_uri: str
