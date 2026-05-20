from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
request_count = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
)

# Kafka metrics
kafka_messages_produced = Counter(
    "kafka_messages_produced_total",
    "Total messages produced to Kafka",
    ["topic"],
)

kafka_messages_consumed = Counter(
    "kafka_messages_consumed_total",
    "Total messages consumed from Kafka",
    ["topic"],
)

kafka_consumer_lag = Gauge(
    "kafka_consumer_lag",
    "Kafka consumer lag in messages",
    ["topic", "consumer_group"],
)

# Agent metrics
agent_processing_duration = Histogram(
    "agent_processing_duration_seconds",
    "Time taken to process a message",
    ["agent_type"],
)

agent_errors = Counter(
    "agent_errors_total",
    "Total errors in agents",
    ["agent_type", "error_type"],
)

# Database metrics
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
)

db_errors = Counter(
    "db_errors_total",
    "Total database errors",
    ["error_type"],
)


class MetricsMiddleware:
    """Middleware for recording API metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time
                
                method = scope["method"]
                path = scope["path"]
                
                request_count.labels(
                    method=method,
                    endpoint=path,
                    status=status_code,
                ).inc()
                
                request_duration.labels(
                    method=method,
                    endpoint=path,
                ).observe(duration)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
