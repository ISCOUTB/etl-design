from datetime import datetime
from app.core.database import mongo_connection
from jsonschema import validate, ValidationError
import threading
from typing import List, Dict, Tuple

import pymongo.results


def compare_schemas(schema1: dict, schema2: dict) -> bool:
    """
    Compare two JSON schemas for equality.
    Returns True if they are equal, False otherwise.
    """
    return schema1 == schema2


def validate_data_chunk(data_chunk: List[Dict], schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a chunk of data against a JSON schema.
    
    Args:
        data_chunk (List[Dict]): A list of data items to validate.
        schema (Dict): The JSON schema to validate against.
    
    Returns:
        Tuple[bool, List[str]]: A tuple containing a boolean indicating if all items are valid,
                               and a list of validation error messages.
    """
    errors = []
    for i, item in enumerate(data_chunk):
        try:
            validate(instance=item, schema=schema)
        except ValidationError as e:
            errors.append(f"Item {i}: {e.message}")
        except Exception as e:
            errors.append(f"Item {i}: Unexpected error - {str(e)}")
    
    return len(errors) == 0, errors


def validate_data_parallel(data: List[Dict], schema: Dict, n_workers: int = 4) -> Dict:
    """
    Validate data against a JSON schema using parallel processing.
    
    Args:
        data (List[Dict]): The data to validate.
        schema (Dict): The JSON schema to validate against.
        n_workers (int): Number of worker threads to use.
    
    Returns:
        Dict: A dictionary containing validation results with success status, 
              total items, valid items, and error details.
    """
    if not data:
        return {
            "is_valid": True,
            "total_items": 0,
            "valid_items": 0,
            "invalid_items": 0,
            "errors": []
        }
    
    # Split data into chunks for parallel processing
    chunk_size = max(1, len(data) // n_workers)
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    results = []
    threads = []
    
    # Function to store results from each thread
    def worker(chunk, index):
        is_valid, errors = validate_data_chunk(chunk, schema)
        results.append((index, is_valid, errors))
    
    # Start threads
    for i, chunk in enumerate(chunks):
        thread = threading.Thread(target=worker, args=(chunk, i))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Process results
    all_errors = []
    total_valid_items = 0
    
    # Sort results by index to maintain order
    results.sort(key=lambda x: x[0])
    
    for index, is_valid, errors in results:
        chunk_size_actual = len(chunks[index])
        if is_valid:
            total_valid_items += chunk_size_actual
        else:
            # Adjust error indices to reflect their position in the original data
            chunk_start = sum(len(chunks[j]) for j in range(index))
            adjusted_errors = []
            for error in errors:
                # Extract the item number and adjust it
                if error.startswith("Item "):
                    try:
                        item_num = int(error.split(":")[0].replace("Item ", ""))
                        adjusted_error = error.replace(f"Item {item_num}:", f"Item {chunk_start + item_num}:")
                        adjusted_errors.append(adjusted_error)
                    except:
                        adjusted_errors.append(error)
                else:
                    adjusted_errors.append(error)
            all_errors.extend(adjusted_errors)
            total_valid_items += chunk_size_actual - len(errors)
    
    total_items = len(data)
    invalid_items = total_items - total_valid_items
    
    return {
        "is_valid": len(all_errors) == 0,
        "total_items": total_items,
        "valid_items": total_valid_items,
        "invalid_items": invalid_items,
        "errors": all_errors[:50]  # Limit errors to first 50 to avoid overwhelming response
    }


def get_active_schema(import_name: str) -> Dict | None:
    """
    Get the active schema for a given import name.
    
    Args:
        import_name (str): The name of the import.
    
    Returns:
        Dict | None: The active schema if found, None otherwise.
    """
    schema_doc = mongo_connection.find_one({"import_name": import_name})
    if schema_doc and "active_schema" in schema_doc:
        return schema_doc["active_schema"]
    return None


def save_schema(
    schema: dict, import_name: str
) -> pymongo.results.InsertOneResult | pymongo.results.UpdateResult:
    """
    Save the schema to the MongoDB collection.
    If the schema is the same as the active schema, no update is needed.
    Otherwise, update the active schema and add it to the schemas_releases.

    Args:
        schema (dict): The JSON schema to save.
        import_name (str): The name of the import, used as a unique identifier.
    Returns:
        pymongo.results.InsertOneResult or pymongo.results.UpdateResult: The result of the insert or update operation.
    """
    schemas_releases = mongo_connection.find_one({"import_name": import_name})

    if mongo_connection.count_documents() == 0 or schemas_releases is None:
        return mongo_connection.insert_one(
            {
                "import_name": import_name,
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
            "import_name": import_name,
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
