import json


def classify_request(text: str) -> str:
    """Classify a request payload into billing, tech, or general."""
    content = text
    try:
        payload = json.loads(text)
        content = str(payload.get("content", text))
    except Exception:
        # Fallback to raw text when payload is not JSON.
        content = text

    normalized = content.lower()

    billing_keywords = ("invoice", "billing", "refund", "payment", "charge")
    tech_keywords = ("error", "bug", "outage", "down", "database", "performance", "slow")

    if any(keyword in normalized for keyword in billing_keywords):
        return "billing"
    if any(keyword in normalized for keyword in tech_keywords):
        return "tech"
    return "general"
