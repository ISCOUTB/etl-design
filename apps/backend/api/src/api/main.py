from fastapi import APIRouter

from src.api.routes.cache import router as cache_router
from src.api.routes.healthcheck import router as healthcheck_router
from src.api.routes.login import router as login_router
from src.api.routes.schemas import router as schemas_router
from src.api.routes.uploads import router as uploads_router
from src.api.routes.users import router as users_router

router = APIRouter()

router.include_router(login_router, prefix="/login", tags=["login"])
router.include_router(cache_router, prefix="/cache", tags=["cache"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(schemas_router, prefix="/schemas", tags=["schemas"])
router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
router.include_router(healthcheck_router, prefix="/healthcheck", tags=["healthcheck"])
