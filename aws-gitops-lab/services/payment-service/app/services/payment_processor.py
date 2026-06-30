import random
import time
import uuid


def generate_transaction():
    return {
        "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"CUS-{random.randint(10000, 99999)}",
        "amount": random.randint(1000, 50000),
        "currency": "NGN",
    }


def simulate_payment():
    time.sleep(random.uniform(0.05, 0.3))
    return generate_transaction()
