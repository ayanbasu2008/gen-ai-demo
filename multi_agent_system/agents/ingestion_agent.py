import asyncio
from services.kafka_service import KafkaProducer
from common.schemas import Request
import json

async def run_ingestion():
    producer = KafkaProducer()
    # Example: simulate incoming request
    request = Request(id="1", source="email", content="Invoice issue", timestamp="2026-05-12T21:55:00")
    await producer.produce("classification_requests", request.model_dump_json())

if __name__ == "__main__":
    asyncio.run(run_ingestion())
