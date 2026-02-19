from typing import Any, Generic, TypeVar

from src.models.projects import Project, UserProject
from src.models.users import User

Model = TypeVar("Model", Project, UserProject, User)


class ModelKey(Generic[Model]):
    def __init__(self, name: str, model_class: type[Model]) -> None:
        self.name = name
        self.model_class = model_class

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ModelKey):
            return self.name == other.name
        return False

    def __str__(self) -> str:
        return self.name


AnyModelKey = ModelKey[Any]


class ModelKeys:
    # ============ Users ============
    user: ModelKey[User] = ModelKey("user", User)

    # ============ Projects ============
    project: ModelKey[Project] = ModelKey("project", Project)
    user_project: ModelKey[UserProject] = ModelKey("user_project", UserProject)
