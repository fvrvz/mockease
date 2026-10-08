from fastapi import APIRouter

from .auth import router as auth_router
from .applications import router as applications_router
from .controllers import router as controllers_router
from .endpoints import router as endpoints_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(applications_router)
v1_router.include_router(controllers_router)
v1_router.include_router(endpoints_router)

