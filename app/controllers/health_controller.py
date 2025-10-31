from fastapi import APIRouter

from app.services.health_service import HealthService

router = APIRouter()

@router.get("/health")
def health_check():
    status = HealthService.health_status()
    overall = all(status.values())
    return {
        "status": "ok" if overall else "degraded",
        "checks": status
    }
