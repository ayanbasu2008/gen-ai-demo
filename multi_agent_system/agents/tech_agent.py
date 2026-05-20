import asyncio
import json
from services.kafka_service import KafkaConsumer, KafkaProducer
from services.db_service import DatabaseService
from common.processors import TechProcessor
from common.logger import get_logger
from common.metrics import agent_processing_duration, agent_errors
import time

logger = get_logger(__name__)


async def run_tech():
    """Process technical requests with dynamic logic."""
    consumer = KafkaConsumer("tech_requests")
    producer = KafkaProducer()
    db_service = DatabaseService()
    
    try:
        await db_service.init()
        logger.info("Tech agent started")
        
        async for msg in consumer:
            start_time = time.time()
            try:
                # Parse request
                request_data = json.loads(msg.value.decode("utf-8"))
                logger.info(
                    "Processing tech request",
                    request_id=request_data.get("id"),
                )
                
                # Generate dynamic response
                response = TechProcessor.process(request_data)
                print("**** TechProcessor response:", response)
                
                # Produce to audit_logs
                await producer.produce("audit_logs", json.dumps(response))
                
                # Store in database
                await db_service.insert_audit_log({
                    "id": request_data.get("id"),
                    "source": request_data.get("source"),
                    "content": request_data.get("content"),
                    "status": response.get("status"),
                    "timestamp": request_data.get("timestamp"),
                })
                
                # Record metrics
                duration = time.time() - start_time
                agent_processing_duration.labels(agent_type="tech").observe(duration)
                logger.info(
                    "Tech request processed",
                    request_id=request_data.get("id"),
                    status=response.get("status"),
                    duration=duration,
                )
                
            except Exception as e:
                logger.error(
                    "Error processing tech request",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                agent_errors.labels(
                    agent_type="tech",
                    error_type=type(e).__name__,
                ).inc()
    
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(run_tech())
