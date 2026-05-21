from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from services.kafka_service import KafkaProducer, ensure_topics
from services.db_service import DatabaseService
from common.schemas import Request
from common.utils import retry_async
from common.security import verify_api_key
from common.logger import setup_logging, get_logger
from common.metrics import MetricsMiddleware, request_count, kafka_messages_produced
from common.settings import settings

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="Agent System API", version="1.0.0")

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

db_service = DatabaseService()


async def ensure_topics_startup() -> bool:
    await ensure_topics()
    return True


async def init_db_startup() -> bool:
    await db_service.init(run_migrations=True)
    return True


@app.on_event("startup")
async def startup_event():
    logger.info("API startup event triggered")
    try:
        topics_ready = await retry_async(
            ensure_topics_startup,
            retries=settings.KAFKA_RETRY_MAX_ATTEMPTS,
            delay=float(settings.KAFKA_RETRY_DELAY_SECONDS),
        )
        if not topics_ready:
            logger.error("Kafka topic initialization failed")
            raise RuntimeError("Kafka topic initialization failed after retries")

        db_ready = await retry_async(
            init_db_startup,
            retries=settings.KAFKA_RETRY_MAX_ATTEMPTS,
            delay=float(settings.KAFKA_RETRY_DELAY_SECONDS),
        )
        if not db_ready:
            logger.error("Database initialization failed")
            raise RuntimeError("Database initialization failed after retries")
        
        logger.info("API startup complete")
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("API shutdown event triggered")
    await db_service.close()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.ENABLE_METRICS:
        raise HTTPException(status_code=403, detail="Metrics disabled")
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/submit")
async def submit_request(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Submit a request for processing."""
    try:
        logger.info(
            "Request submitted",
            request_id=request.id,
            source=request.source,
        )
        
        producer = KafkaProducer()
        await producer.produce("classification_requests", request.model_dump_json())
        
        # Record metrics
        kafka_messages_produced.labels(topic="classification_requests").inc()
        
        logger.info(
            "Request sent to classification",
            request_id=request.id,
        )
        
        return {
            "status": "submitted",
            "id": request.id,
            "message": "Request queued for processing",
        }
    except Exception as e:
        logger.error(
            "Error submitting request",
            request_id=request.id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit request",
        )


@app.get("/requests/{request_id}")
async def get_request_status(
    request_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get the status of a submitted request."""
    try:
        status = await db_service.get_audit_log(request_id)
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )
        return status
    except Exception as e:
        logger.error(
            "Error fetching request status",
            request_id=request_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch request status",
        )

