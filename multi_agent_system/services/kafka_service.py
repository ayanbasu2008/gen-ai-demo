import os
from aiokafka.admin import NewTopic
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient
from common.config import KAFKA_BOOTSTRAP
from common.settings import settings
from common.logger import get_logger
from common.metrics import kafka_messages_produced, kafka_messages_consumed
import asyncio

logger = get_logger(__name__)

REQUIRED_TOPICS = [
    "classification_requests",
    "billing_requests",
    "tech_requests",
    "general_requests",
    "audit_logs",
    "escalations",
]


async def ensure_topics(topics: list[str] | None = None, bootstrap_servers: str | None = None):
    """Create required Kafka topics if they do not already exist."""
    try:
        bootstrap = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP", KAFKA_BOOTSTRAP)
        admin = AIOKafkaAdminClient(bootstrap_servers=bootstrap)
        await admin.start()
        try:
            existing_topics = set(await admin.list_topics())
            requested_topics = topics or REQUIRED_TOPICS
            new_topics = [
                NewTopic(topic, num_partitions=1, replication_factor=1)
                for topic in requested_topics
                if topic not in existing_topics
            ]
            if new_topics:
                await admin.create_topics(new_topics)
                logger.info(f"Created {len(new_topics)} Kafka topics")
        finally:
            await admin.close()
    except Exception as e:
        logger.error(f"Error ensuring Kafka topics: {str(e)}")
        raise


class KafkaConsumer:
    def __init__(self, topic: str, group_id: str | None = None):
        self.topic = topic
        self.group_id = group_id or f"{topic}-group"
        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

    async def __aiter__(self):
        try:
            await self.consumer.start()
            logger.info(f"Kafka consumer started for topic: {self.topic}")
            try:
                async for msg in self.consumer:
                    kafka_messages_consumed.labels(topic=self.topic).inc()
                    yield msg
            finally:
                await self.consumer.stop()
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {str(e)}")
            raise


class KafkaProducer:
    def __init__(self):
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP
        self.max_retries = settings.KAFKA_RETRY_MAX_ATTEMPTS

    async def produce(self, topic: str, value: str):
        """Produce a message to Kafka with retry logic."""
        for attempt in range(self.max_retries):
            producer = None
            try:
                producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                )
                await producer.start()
                await producer.send_and_wait(topic, value.encode("utf-8"))
                kafka_messages_produced.labels(topic=topic).inc()
                logger.debug(f"Message produced to {topic}")
                return
            except Exception as e:
                logger.warning(
                    f"Error producing message (attempt {attempt + 1}/{self.max_retries})",
                    error=str(e),
                    topic=topic,
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(settings.KAFKA_RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"Failed to produce message after {self.max_retries} attempts")
                    raise
            finally:
                if producer:
                    try:
                        await producer.stop()
                    except Exception as e:
                        logger.debug(f"Error stopping producer: {str(e)}")

