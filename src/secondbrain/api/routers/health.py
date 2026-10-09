from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from secondbrain.api.dependencies import get_file_storage
from secondbrain.database.dependencies import get_db
from secondbrain.storage.file_storage import LocalFileStorage

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(
    db: Session = Depends(get_db),
    storage: LocalFileStorage = Depends(get_file_storage),
) -> dict[str, object]:
    checks: dict[str, str] = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        storage.base_path.mkdir(parents=True, exist_ok=True)
        checks["storage"] = "ok"
    except OSError:
        checks["storage"] = "error"

    ready = all(value == "ok" for value in checks.values())

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready",
        )

    return {"status": "ready", "checks": checks}
