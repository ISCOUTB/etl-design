from fastapi import APIRouter
from app.api.routes.schemas import router as schemas_router
from app.api.routes.validation import router as validation_router


router = APIRouter()

router.include_router(schemas_router, prefix="/schemas", tags=["schemas"])
router.include_router(validation_router, prefix="/validation", tags=["validation"])
