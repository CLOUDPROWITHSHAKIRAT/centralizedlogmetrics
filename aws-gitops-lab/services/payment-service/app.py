from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import logging
import random
import time

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s service=payment-service message=%(message)s"
)

REQUEST_COUNT = Counter("payment_requests_total", "Total payment requests", ["status"])
REQUEST_LATENCY = Histogram("payment_request_latency_seconds", "Payment request latency")

@app.get("/")
def home():
    logging.info("Payment service homepage accessed")
    return {"service": "payment-service", "status": "running"}

@app.get("/health")
def health():
    logging.info("Health check successful")
    return {"status": "healthy"}

@app.get("/pay")
@REQUEST_LATENCY.time()
def pay():
    outcome = random.choice(["success", "success", "success", "warning", "error"])

    if outcome == "success":
        REQUEST_COUNT.labels(status="success").inc()
        logging.info("Payment completed successfully")
        return {"payment": "success", "message": "Payment completed"}

    if outcome == "warning":
        REQUEST_COUNT.labels(status="warning").inc()
        logging.warning("Payment retry triggered due to slow dependency")
        return {"payment": "retry", "message": "Payment retry triggered"}

    REQUEST_COUNT.labels(status="error").inc()
    logging.error("Payment failed due to fraud service timeout")
    return Response(
        content='{"payment":"failed","error":"fraud service timeout"}',
        status_code=500,
        media_type="application/json"
    )

@app.get("/cpu")
def cpu_spike():
    logging.warning("CPU spike endpoint triggered")
    end = time.time() + 10
    while time.time() < end:
        _ = sum(i * i for i in range(10000))
    return {"status": "cpu spike completed"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)