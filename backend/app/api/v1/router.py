"""
API v1 Router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import datasets, cycles, analysis

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(cycles.router, prefix="/cycles", tags=["cycles"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
