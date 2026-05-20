import os


def _default_kafka_bootstrap() -> str:
	"""Choose a sensible Kafka default based on runtime environment."""
	# Containers can resolve the Kafka service name; host processes should use localhost.
	if os.path.exists("/.dockerenv"):
		return "kafka:9092"
	return "localhost:29092"


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", _default_kafka_bootstrap())
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://agent:agentpass@postgres:5432/agents")
