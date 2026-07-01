import random
import time
import uuid
import requests


FRAUD_SERVICE_URL = "http://fraud-service.dev.svc.cluster.local/check"


def generate_transaction():
    return {
        "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"CUS-{random.randint(10000, 99999)}",
        "amount": random.randint(1000, 50000),
        "currency": "NGN",
    }


def check_fraud_service():
    response = requests.get(FRAUD_SERVICE_URL, timeout=2)
    response.raise_for_status()
    return response.json()


def simulate_payment():
    time.sleep(random.uniform(0.05, 0.3))
    transaction = generate_transaction()
    fraud_result = check_fraud_service()
    transaction["fraud_check"] = fraud_result.get("fraud_check")
    transaction["fraud_reason"] = fraud_result.get("reason", "")
    return transaction
