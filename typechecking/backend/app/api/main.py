from fastapi import APIRouter
from app.api.routes.login import router as login_router
from app.api.routes.cache import router as cache_router
from app.api.routes.schemas import router as schemas_router
from app.api.routes.validation import router as validation_router
from app.api.routes.healthcheck import router as healthcheck_router


router = APIRouter()

router.include_router(login_router, prefix="/login", tags=["login"])
router.include_router(cache_router, prefix="/cache", tags=["cache"])
router.include_router(schemas_router, prefix="/schemas", tags=["schemas"])
router.include_router(validation_router, prefix="/validation", tags=["validation"])
router.include_router(healthcheck_router, prefix="/healthcheck", tags=["healthcheck"])
