import time
from fastapi import APIRouter

from app.logging_config import setup_logging

router = APIRouter()
logger = setup_logging()


@router.get("/cpu")
def cpu_spike():
    logger.warning("CPU spike endpoint triggered")

    end = time.time() + 10
    while time.time() < end:
        _ = sum(i * i for i in range(10000))

    return {"status": "cpu spike completed"}


@router.get("/memory")
def memory_spike():
    logger.warning("Memory spike endpoint triggered")

    data = ["x" * 1024 * 1024 for _ in range(100)]
    time.sleep(5)

    return {"status": "memory spike completed", "allocated_mb": len(data)}
