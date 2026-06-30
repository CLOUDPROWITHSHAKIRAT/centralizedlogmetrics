from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.metrics import router as metrics_router
from app.routes.payment import router as payment_router
from app.routes.admin import router as admin_router

app = FastAPI(title="Payment Service", version="1.0.0")

app.include_router(payment_router)
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(admin_router)
