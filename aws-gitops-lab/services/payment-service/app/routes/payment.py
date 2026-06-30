import time
from fastapi import APIRouter
from starlette.responses import Response

from app.logging_config import setup_logging
from app.metrics import (
    payment_requests_total,
    payment_failures_total,
    payment_latency_seconds,
    payment_inflight_requests,
)
from app.services.payment_processor import simulate_payment

router = APIRouter()
logger = setup_logging()


@router.get("/")
def home():
    logger.info("Payment service homepage accessed")
    return {"service": "payment-service", "status": "running"}


@router.get("/pay")
def pay():
    payment_inflight_requests.inc()
    start = time.time()

    try:
        transaction = simulate_payment()
        duration = time.time() - start

        payment_requests_total.labels(status="success").inc()
        payment_latency_seconds.observe(duration)

        logger.info(
            "Payment completed successfully",
            extra={
                "extra_fields": {
                    **transaction,
                    "status": "SUCCESS",
                    "duration_ms": round(duration * 1000, 2),
                }
            },
        )

        return {
            "payment": "success",
            "transaction": transaction,
            "duration_ms": round(duration * 1000, 2),
        }

    finally:
        payment_inflight_requests.dec()


@router.get("/pay/error")
def pay_error():
    payment_inflight_requests.inc()
    start = time.time()

    try:
        transaction = simulate_payment()
        duration = time.time() - start

        payment_requests_total.labels(status="error").inc()
        payment_failures_total.labels(reason="fraud_service_timeout").inc()
        payment_latency_seconds.observe(duration)

        logger.error(
            "Payment failed due to fraud service timeout",
            extra={
                "extra_fields": {
                    **transaction,
                    "status": "FAILED",
                    "error": "fraud_service_timeout",
                    "duration_ms": round(duration * 1000, 2),
                }
            },
        )

        return Response(
            content='{"payment":"failed","error":"fraud_service_timeout"}',
            status_code=500,
            media_type="application/json",
        )

    finally:
        payment_inflight_requests.dec()


@router.get("/pay/slow")
def pay_slow():
    payment_inflight_requests.inc()
    start = time.time()

    try:
        time.sleep(3)
        transaction = simulate_payment()
        duration = time.time() - start

        payment_requests_total.labels(status="slow").inc()
        payment_latency_seconds.observe(duration)

        logger.warning(
            "Payment request completed slowly",
            extra={
                "extra_fields": {
                    **transaction,
                    "status": "SLOW",
                    "warning": "slow_dependency",
                    "duration_ms": round(duration * 1000, 2),
                }
            },
        )

        return {
            "payment": "slow",
            "transaction": transaction,
            "duration_ms": round(duration * 1000, 2),
        }

    finally:
        payment_inflight_requests.dec()
