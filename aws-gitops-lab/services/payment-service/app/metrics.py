from prometheus_client import Counter, Histogram, Gauge

payment_requests_total = Counter(
    "payment_requests_total",
    "Total number of payment requests",
    ["status"],
)

payment_failures_total = Counter(
    "payment_failures_total",
    "Total number of failed payment requests",
    ["reason"],
)

payment_latency_seconds = Histogram(
    "payment_latency_seconds",
    "Payment request latency in seconds",
)

payment_inflight_requests = Gauge(
    "payment_inflight_requests",
    "Number of payment requests currently in progress",
)
