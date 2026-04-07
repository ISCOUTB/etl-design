"""MongoDB database operations module.

This module provides MongoDB client operations for document storage and retrieval.
It includes a connection wrapper class that simplifies common MongoDB operations
and provides pre-configured connections for tasks and schemas collections.

The module uses PyMongo for database interactions and includes basic CRUD operations
with proper error handling, type hints, and transaction support for ACID compliance.
"""

from contextlib import contextmanager
from typing import Dict, Optional

import pymongo
import pymongo.collection
import pymongo.database
import pymongo.errors
import pymongo.results
from pymongo.client_session import ClientSession


class MongoConnection:
    """MongoDB connection wrapper class.

    Provides a simplified interface for MongoDB operations including
    basic CRUD operations and collection management. Encapsulates
    the MongoDB client, database, and collection objects.

    Args:
        uri (str): MongoDB connection URI.
        database (str): Name of the database to connect to.
        collection (str): Name of the collection to work with.
    """

    def __init__(self, uri: str, database: str, collection: str):
        self.__client: pymongo.MongoClient = pymongo.MongoClient(uri)
        self.__database: pymongo.database.Database = self.__client[database]
        self.__collection: pymongo.collection.Collection = self.__database[collection]

    def is_healthy(self) -> bool:
        """Internal method to check MongoDB health.

        Returns:
            bool: True if MongoDB is healthy, False otherwise.
        """
        try:
            self.__client.admin.command("ping")
            return True
        except (
            pymongo.errors.ConnectionFailure,
            pymongo.errors.ServerSelectionTimeoutError,
        ):
            return False

    # ==================== General Purpose ====================
    # To be honest, these functions are a little bit useless, but maybe in a future
    # we would want to make something better, and with this could be easier, than
    # using directly MongoClient. Who knows

    @property
    def client(self) -> pymongo.MongoClient:
        """Get the MongoDB client instance.

        Returns:
            pymongo.MongoClient: The MongoDB client instance.
        """
        return self.__client

    @property
    def database(self) -> pymongo.database.Database:
        """Get the MongoDB database instance.

        Returns:
            pymongo.database.Database: The MongoDB database instance.

        Raises:
            ValueError: If database is not set.
        """
        if self.__database is None:
            raise ValueError("Database not set. Please provide a database name.")
        return self.__database

    @property
    def collection(self) -> pymongo.collection.Collection:
        """Get the MongoDB collection instance.

        Returns:
            pymongo.collection.Collection: The MongoDB collection instance.

        Raises:
            ValueError: If database is not set.
        """
        if self.__database is None:
            raise ValueError(
                "Database not set. Please set a database before accessing collections."
            )
        return self.__collection

    def insert_one(
        self, document: Dict, session: Optional[ClientSession] = None
    ) -> pymongo.results.InsertOneResult:
        """Insert a single document into the collection (supports transactions).

        Args:
            document (Dict): Document to insert.
            session (ClientSession, optional): MongoDB session for transaction support.

        Returns:
            pymongo.results.InsertOneResult: Result of the insert operation.
        """
        if session:
            return self.__collection.insert_one(document, session=session)
        return self.__collection.insert_one(document)

    def count_documents(self, filter: Optional[Dict] = None) -> int:
        """Count the number of documents in the collection.

        Args:
            filter (Dict, optional): Query filter to count specific documents.
                                   Defaults to None (counts all documents).

        Returns:
            int: Number of documents matching the filter.
        """
        return self.__collection.count_documents(filter if filter is not None else {})

    def find_one(
        self, filter: Optional[Dict] = None, projection: Optional[Dict] = None
    ):
        """Find a single document in the collection.

        Args:
            filter (Dict, optional): Query filter to find specific document.
                                   Defaults to None (finds any document).
            projection (Dict, optional): Fields to include/exclude in the result.
                                       Defaults to None (returns all fields).

        Returns:
            Dict or None: The found document or None if not found.
        """
        return self.__collection.find_one(
            filter if filter is not None else {}, projection
        )

    def find(
        self,
        filter: Optional[Dict] = None,
        projection: Optional[Dict] = None,
        limit: Optional[int] = None,
    ):
        """Find multiple documents in the collection.

        Args:
            filter (Dict, optional): Query filter to find specific documents.
                                   Defaults to None (finds all documents).
            projection (Dict, optional): Fields to include/exclude in the results.
                                       Defaults to None (returns all fields).
            limit (int, optional): Maximum number of documents to return.
                                   Defaults to None (returns all matching documents).

        Returns:
            pymongo.cursor.Cursor: Cursor to iterate over the found documents.
        """
        cursor = self.__collection.find(
            filter if filter is not None else {}, projection
        )
        if limit is not None:
            cursor = cursor.limit(limit)
        return cursor

    def update_one(
        self, filter: Dict, update: Dict, session: Optional[ClientSession] = None
    ) -> pymongo.results.UpdateResult:
        """Update a single document in the collection (supports transactions).

        Args:
            filter (Dict): Query filter to identify the document to update.
            update (Dict): Update operations to apply to the document.
            session (ClientSession, optional): MongoDB session for transaction support.

        Returns:
            pymongo.results.UpdateResult: Result of the update operation.
        """
        if session:
            return self.__collection.update_one(filter, update, session=session)
        return self.__collection.update_one(filter, update)

    def delete_one(
        self, filter: Dict, session: Optional[ClientSession] = None
    ) -> pymongo.results.DeleteResult:
        """Delete a single document in the collection (supports transactions).

        Args:
            filter (Dict): Query filter to identify the document to delete.
            session (ClientSession, optional): MongoDB session for transaction support.

        Returns:
            pymongo.results.DeleteResult: Result of the delete operation.
        """
        if session:
            return self.__collection.delete_one(filter, session=session)
        return self.__collection.delete_one(filter)

    # ==================== Transactions ====================

    @contextmanager
    def transaction(self):
        """Context manager for atomic MongoDB transactions.

        MongoDB transactions require a replica set. This context manager
        provides ACID guarantees for multi-document operations.

        Usage:
            with mongo_conn.transaction() as session:
                mongo_conn.update_one(filter1, update1, session=session)
                mongo_conn.update_one(filter2, update2, session=session)
                # Auto commits if no exception, auto aborts on exception

        Yields:
            ClientSession: MongoDB session for transactional operations.

        Raises:
            pymongo.errors.OperationFailure: If MongoDB is not configured
                for transactions (requires replica set).
        """
        session = self.__client.start_session()
        try:
            with session.start_transaction():
                yield session
        finally:
            session.end_session()
