import asyncio
import json
import logging
from typing import Any, Callable

# Configure global logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("multi_agent_utils")

def safe_json_loads(data: str) -> dict:
    """Safely parse JSON string into dict."""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        logger.error("Invalid JSON received: %s", data)
        return {}

def safe_json_dumps(obj: Any) -> str:
    """Safely convert object to JSON string."""
    try:
        return json.dumps(obj)
    except Exception as e:
        logger.error("Error serializing object: %s", e)
        return "{}"

async def retry_async(func: Callable, retries: int = 3, delay: float = 1.0, *args, **kwargs):
    """
    Retry an async function with exponential backoff.
    Useful for Kafka/DB operations that may fail intermittently.
    """
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.warning("Attempt %d failed: %s", attempt + 1, e)
            await asyncio.sleep(delay * (2 ** attempt))
    logger.error("All retries failed for function %s", func.__name__)
    return None

def mask_sensitive(data: dict, keys: list[str] = ["password", "token"]) -> dict:
    """Mask sensitive fields in a dictionary before logging."""
    masked = data.copy()
    for key in keys:
        if key in masked:
            masked[key] = "***"
    return masked
