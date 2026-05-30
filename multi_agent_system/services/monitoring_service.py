from prometheus_client import Counter, Histogram, start_http_server
import logging
import time

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] monitoring: %(message)s"
)
logger = logging.getLogger("monitoring_service")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "agent_requests_total",
    "Total number of requests processed by agents",
    ["agent", "status"]
)

REQUEST_LATENCY = Histogram(
    "agent_request_latency_seconds",
    "Latency of agent request processing",
    ["agent"]
)

ERROR_COUNT = Counter(
    "agent_errors_total",
    "Total number of errors encountered by agents",
    ["agent"]
)

def record_request(agent: str, status: str = "success"):
    """Increment request counter for a given agent."""
    REQUEST_COUNT.labels(agent=agent, status=status).inc()
    logger.info("Request recorded for agent=%s status=%s", agent, status)

def record_latency(agent: str, duration: float):
    """Record latency for a given agent."""
    REQUEST_LATENCY.labels(agent=agent).observe(duration)
    logger.info("Latency recorded for agent=%s duration=%.3f", agent, duration)

def record_error(agent: str):
    """Increment error counter for a given agent."""
    ERROR_COUNT.labels(agent=agent).inc()
    logger.error("Error recorded for agent=%s", agent)

def start_monitoring_server(port: int = 8001):
    """Start Prometheus metrics server."""
    start_http_server(port)
    logger.info("Prometheus monitoring server started on port %d", port)

# Example usage
if __name__ == "__main__":
    start_monitoring_server()
    # Simulate agent activity
    for i in range(5):
        start_time = time.time()
        try:
            # simulate work
            time.sleep(0.2)
            record_request("classification_agent", "success")
        except Exception:
            record_error("classification_agent")
        finally:
            duration = time.time() - start_time
            record_latency("classification_agent", duration)
