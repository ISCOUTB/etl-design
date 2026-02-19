from typing import List

from src import models, schemas


class ParserService:
    @staticmethod
    def parse_user(user: models.User) -> schemas.ResponseUserSchema:
        return schemas.ResponseUserSchema.model_validate(user)

    @staticmethod
    def parse_users(users: List[models.User]) -> List[schemas.ResponseUserSchema]:
        return list(map(ParserService.parse_user, users))

    @staticmethod
    def parse_project(project: models.Project) -> schemas.ResponseProjectSchema:
        return schemas.ResponseProjectSchema.model_validate(project)

    @staticmethod
    def parse_projects(
        projects: List[models.Project],
    ) -> List[schemas.ResponseProjectSchema]:
        return list(map(ParserService.parse_project, projects))

    @staticmethod
    def parse_user_project(
        user_project: models.UserProject,
    ) -> schemas.ResponseUserProjectSchema:
        return schemas.ResponseUserProjectSchema.model_validate(user_project)

    @staticmethod
    def parse_user_projects(
        user_projects: List[models.UserProject],
    ) -> List[schemas.ResponseUserProjectSchema]:
        return list(map(ParserService.parse_user_project, user_projects))
