from fastapi import APIRouter
from .endpoints import metrics, grouping, visualization

# Створення головного роутера
router = APIRouter()

# Підключення роутерів з різних модулів
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
router.include_router(grouping.router, prefix="/grouping", tags=["grouping"])
router.include_router(visualization.router, prefix="/visualization", tags=["visualization"]) 