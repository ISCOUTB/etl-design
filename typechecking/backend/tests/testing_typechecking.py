import os
from datetime import datetime

import polars as pl
from json import loads
from jsonschema import validate

from app.core.database_mongo import mongo_connection

import threading


def compare_schemas(schema1: dict, schema2: dict) -> bool:
    """
    Compare two JSON schemas for equality.
    Returns True if they are equal, False otherwise.
    """
    return schema1 == schema2


def save_schema(schema: dict, filename_csv: str) -> None:
    # Filename must have extention
    filename, ext = os.path.splitext(filename_csv)
    schemas_releases = mongo_connection.find_one({"import_name": filename})

    if mongo_connection.count_documents() == 0 or schemas_releases is None:
        return mongo_connection.insert_one(
            {
                "import_name": filename,
                "file_type": ext,
                "created_at": datetime.now().isoformat(),
                "active_schema": schema.copy(),
                "schemas_releases": [],
            }
        )

    if compare_schemas(schemas_releases["active_schema"], schema):
        print("Schema is the same, no update needed.")
        return

    return mongo_connection.update_one(
        {
            "import_name": filename,
        },
        {
            "$set": {
                "active_schema": schema.copy(),
                "created_at": datetime.now().isoformat(),
            },
            "$push": {
                "schemas_releases": {
                    "schema": schema.copy(),
                }
            },
        },
    )


def validate_data(data: list[dict], schema: dict) -> bool:
    for item in data:
        try:
            validate(instance=item, schema=schema)
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    return True


def main() -> None:
    csv_path = "./static/acme__users__sample1.csv"
    schema_path = "./static/acme__users_sample1.json"

    # df = pd.read_csv(csv_path)
    df = pl.read_csv(csv_path)
    print(df)

    with open(schema_path, "r") as file:
        schema = loads(file.read())
        print(schema)

    n_workers = 4
    chunk_size = len(df) // n_workers
    chunks = [df[i : i + chunk_size] for i in range(0, len(df), chunk_size)]

    threads = []
    for chunk in chunks:
        thread = threading.Thread(
            target=validate_data, args=(chunk.to_dicts(), schema)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("All threads completed.")
    save_schema(schema, os.path.basename(csv_path))


if __name__ == "__main__":
    main()
