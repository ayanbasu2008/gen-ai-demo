import asyncio
import json
from services.kafka_service import KafkaConsumer, KafkaProducer
from services.db_service import DatabaseService
from common.llm import ai_process_domain_request
from common.logger import get_logger
from common.metrics import agent_processing_duration, agent_errors
import time

logger = get_logger(__name__)


async def run_billing():
    """Process billing requests with dynamic logic."""
    consumer = KafkaConsumer("billing_requests")
    producer = KafkaProducer()
    db_service = DatabaseService()
    
    try:
        await db_service.init()
        logger.info("Billing agent started")
        
        async for msg in consumer:
            start_time = time.time()
            try:
                # Parse request
                request_data = json.loads(msg.value.decode("utf-8"))
                logger.info(
                    "Processing billing request",
                    request_id=request_data.get("id"),
                )
                
                response = ai_process_domain_request("billing", request_data)
                
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
                agent_processing_duration.labels(agent_type="billing").observe(duration)
                logger.info(
                    "Billing request processed",
                    request_id=request_data.get("id"),
                    status=response.get("status"),
                    duration=duration,
                )
                
            except Exception as e:
                logger.error(
                    "Error processing billing request",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                agent_errors.labels(
                    agent_type="billing",
                    error_type=type(e).__name__,
                ).inc()
    
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(run_billing())
