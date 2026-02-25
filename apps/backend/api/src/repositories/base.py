from typing import Callable, Generic, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.schemas.generic import DeleteResult, T


class BaseRepository(Generic[T]):
    """Base repository class providing common CRUD operations.

    This abstract base class implements reusable data access patterns
    for SQLAlchemy models. All repository classes should inherit from
    this class to ensure consistent behavior across the application.

    The base repository provides:
    - Read operations: get by ID
    - Update operations: partial updates (PATCH semantics)
    - Delete operations: conditional deletes checking dependencies

    Note:
        All methods that modify data (update, delete) use flush() instead
        of commit(). The caller is responsible for transaction management.
    """

    def __init__(self, db: Session) -> None:
        """Initialize the base repository.

        Args:
            db: SQLAlchemy session for database operations.
        """
        self.db = db

    def _get_by_id(self, model: type[T], *, obj_id: str) -> Optional[T]:
        """Retrieve a single record by its primary key.

        Args:
            model (T): SQLAlchemy model class to query.
            obj_id (str): Primary key value (typically UUID string).

        Returns:
            Optional[T]: Model instance if found, None otherwise.

        Note:
            Uses SQLAlchemy's Session.get() for efficient primary key lookup.
        """
        return self.db.get(model, obj_id)

    def _simple_update(
        self,
        model: type[T],
        *,
        obj_id: Optional[str],
        update_data: BaseModel,
        db_obj: Optional[T] = None,
    ) -> Optional[T]:
        """Update a record with partial data (PATCH semantics).

        Only fields explicitly set in the update_data schema are modified.
        Unset fields remain unchanged, enabling true PATCH behavior.

        Args:
            model (T): SQLAlchemy model class to update.
            obj_id (Optional[str]): Primary key of the record to update.
            update_data (BaseModel): Pydantic schema containing fields to update.
                Uses exclude_unset=True to only update provided fields.
            db_obj (Optional[T]): Pre-fetched model instance to update. If provided,
                obj_id is ignored.

        Returns:
            Optional[T]: Updated model instance if found, None if record doesn't exist.

        Raises:
            TypeError: If neither obj_id nor db_obj is provided.

        Note:
            Does not commit the transaction. Caller must handle commit/rollback.
            Uses flush() to persist changes and obtain generated values.
        """
        if obj_id is None and db_obj is None:
            raise TypeError("Either obj_id or db_obj must be provided")

        if db_obj is None:
            db_obj = self._get_by_id(model, obj_id=obj_id)  # type: ignore
            if not db_obj:
                return None

        update_data_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_data_dict.items():
            setattr(db_obj, field, value)

        return db_obj

    def _conditional_delete(
        self,
        model: type[T],
        *,
        obj_id: Optional[str] = None,
        db_obj: Optional[T] = None,
        relationship_attrs: Optional[List[str]] = None,
        filter_related_items: Optional[Callable[[T], bool]] = None
    ) -> DeleteResult[T]:
        """Delete a record only if it has no dependent child records.

        This method implements safe deletion by checking for dependencies
        before allowing the delete operation. Prevents orphaned records
        and maintains referential integrity at the application level.

        Args:
            model (T): SQLAlchemy model class to delete from.
            obj_id (Optional[str]): Primary key of the record to delete.
                Ignored if db_obj is provided.
            db_obj (Optional[T]): Pre-fetched model instance to delete.
                If provided, obj_id is ignored.
            relationship_attrs (Optional[List[str]]): List of relationship attributes
                to check for dependencies.
                If the relationship contains any records, deletion is blocked.

        Returns:
            DeleteResult[T]: Result object indicating success status, reason,
                and deleted object if successful.

        Note:
            Does not commit the transaction. Caller must handle commit/rollback.
            Uses flush() to persist the deletion.
        """
        if db_obj is None:
            assert obj_id is not None, "obj_id must be provided if db_obj is not given"

            db_obj = self._get_by_id(model, obj_id=obj_id)
            if not db_obj:
                return DeleteResult(success=False, status="not_found")

        filter_related_items = filter_related_items or (lambda x: True)

        if not relationship_attrs:
            relationship_attrs = []

        # Check for dependencies if relationship attribute specified
        for relationship_attr in relationship_attrs:
            if hasattr(db_obj, relationship_attr):
                related_items = getattr(db_obj, relationship_attr)
                filtered_items = list(filter(filter_related_items, related_items))
                if filtered_items:
                    return DeleteResult(success=False, status="has_dependencies")

        self.db.delete(db_obj)
        return DeleteResult(success=True, status="deleted", obj=db_obj)
