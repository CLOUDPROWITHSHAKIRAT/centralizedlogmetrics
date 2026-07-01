from fastapi import FastAPI
import random
import time

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "healthy", "service": "fraud-service"}


@app.get("/check")
def check():
    outcome = random.choice(["approved", "approved", "approved", "delay", "blocked"])

    if outcome == "delay":
        time.sleep(3)
        return {"fraud_check": "delayed"}

    if outcome == "blocked":
        return {"fraud_check": "blocked", "reason": "suspicious_transaction"}

    return {"fraud_check": "approved"}
