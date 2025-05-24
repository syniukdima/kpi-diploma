from fastapi import APIRouter
from .endpoints import metrics, grouping, visualization, autonormalization

api_router = APIRouter()

api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(grouping.router, prefix="/grouping", tags=["grouping"])
api_router.include_router(visualization.router, prefix="/visualization", tags=["visualization"])
api_router.include_router(autonormalization.router, prefix="/autonormalization", tags=["autonormalization"]) 