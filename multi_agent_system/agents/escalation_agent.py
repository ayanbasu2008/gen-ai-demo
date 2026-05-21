import asyncio
import json
import logging
from services.kafka_service import KafkaConsumer, KafkaProducer
from common.llm import generate_summary_escalation, suggest_escalation_action

logger = logging.getLogger(__name__)

ESCALATION_THRESHOLD = 2  # number of failed attempts before escalation

async def run_escalation():
    print("Starting escalation agent...")
    # Separate group ensures escalation sees every audit event.
    consumer = KafkaConsumer("audit_logs", group_id="escalation-agent-group")
    producer = KafkaProducer()
    

    async for msg in consumer:
        log = json.loads(msg.value.decode("utf-8"))
        
        # Example: check if issue is unresolved or repeatedly failed
        if log.get("status") == "unresolved" or log.get("status") == "escalated" or log.get("status") == "critical" or log.get("attempts", 0) >= ESCALATION_THRESHOLD:
            issue_text = log.get("details")
            # LLM-powered summary and action suggestion
            try:
                summary = generate_summary_escalation(issue_text)
                logger.info(f"Generated summary for escalation: {summary}")
            except Exception as e:
                logger.error(f"Error generating summary: {e}", exc_info=True)
                summary = "[LLM summary unavailable]"
            try:
                recommended_action = suggest_escalation_action(issue_text)
                logger.info(f"Generated recommended action for escalation: {recommended_action}")
            except Exception as e:
                logger.error(f"Error generating recommended action: {e}", exc_info=True)
                recommended_action = "[LLM recommendation unavailable]"

            escalation_payload = {
                "id": log.get("request_id") or log.get("id"),
                "issue": issue_text,
                "summary": summary,
                "recommended_action": recommended_action,
                "source": log.get("source", "system"),
                "timestamp": log.get("processed_at") or log.get("timestamp"),
                "action": "Escalated to human support"
            }
            print("ESCALATION TRIGGERED:", escalation_payload)
            await producer.produce("escalations", json.dumps(escalation_payload))

if __name__ == "__main__":
    asyncio.run(run_escalation())
