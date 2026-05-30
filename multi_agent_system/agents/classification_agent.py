import asyncio
import json
from services.kafka_service import KafkaConsumer, KafkaProducer
from common.llm import ai_classify_request
from common.logger import get_logger

logger = get_logger(__name__)

async def run_classification():
    consumer = KafkaConsumer("classification_requests", group_id="classification-agent-group")
    producer = KafkaProducer()
    logger.info("Classification agent started")

    async for msg in consumer:
        try:
            payload_text = msg.value.decode("utf-8")
            payload = json.loads(payload_text)
            category = ai_classify_request(payload)
            logger.info(
                "Request classified",
                request_id=payload.get("id"),
                category=category,
            )
            await producer.produce(f"{category}_requests", payload_text)
        except Exception as e:
            logger.error("Classification failed", error=str(e), error_type=type(e).__name__)

if __name__ == "__main__":
    asyncio.run(run_classification())
