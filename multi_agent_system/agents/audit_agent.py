import asyncio
import json
from services.kafka_service import KafkaConsumer
from services.db_service import DatabaseService
from common.logger import get_logger
from common.metrics import kafka_messages_consumed
from common.llm import ai_audit_assessment

logger = get_logger(__name__)


async def run_audit():
    """Consume and log audit messages."""
    # Use a dedicated consumer group so this observer does not compete with escalation.
    consumer = KafkaConsumer("audit_logs", group_id="audit-observer-group")
    db_service = DatabaseService()
    
    try:
        await db_service.init()
        logger.info("Audit agent started")
        
        async for msg in consumer:
            try:
                audit_data = json.loads(msg.value.decode("utf-8"))
                print("Processing audit log for audit:", audit_data)
                assessment = ai_audit_assessment(audit_data)
                audit_data["ai_assessment"] = assessment
                
                # Log to console
                logger.info(
                    "AUDIT LOG",
                    audit_entry=audit_data,
                )
                
                # Record metrics
                kafka_messages_consumed.labels(topic="audit_logs").inc()
                
            except Exception as e:
                logger.error(
                    "Error processing audit log",
                    error=str(e),
                    error_type=type(e).__name__,
                )
    
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(run_audit())
