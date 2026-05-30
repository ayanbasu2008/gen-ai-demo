import asyncio
import json
import logging
from services.kafka_service import KafkaConsumer, KafkaProducer
from common.llm import (
    ai_escalation_decision,
    generate_summary_escalation,
    suggest_escalation_action,
)

logger = logging.getLogger(__name__)

async def run_escalation():
    print("Starting escalation agent...")
    # Separate group ensures escalation sees every audit event.
    consumer = KafkaConsumer("audit_logs", group_id="escalation-agent-group")
    producer = KafkaProducer()
    

    async for msg in consumer:
        log = json.loads(msg.value.decode("utf-8"))
        print("***//// Processing audit log for escalation:", log)
        decision = ai_escalation_decision(log)
        
        if decision.get("should_escalate"):
            issue_text = log.get("details") or log.get("content") or "No details provided"
            summary = generate_summary_escalation(issue_text)
            recommended_action = suggest_escalation_action(issue_text)
            logger.info(
                "AI escalation decision",
                request_id=log.get("request_id") or log.get("id"),
                risk_level=decision.get("risk_level"),
                reason=decision.get("reason"),
            )

            escalation_payload = {
                "id": log.get("request_id") or log.get("id"),
                "issue": issue_text,
                "summary": summary,
                "recommended_action": recommended_action,
                "source": log.get("source", "system"),
                "timestamp": log.get("processed_at") or log.get("timestamp"),
                "action": "Escalated to human support",
                "risk_level": decision.get("risk_level"),
                "reason": decision.get("reason"),
            }
            print("ESCALATION TRIGGERED:", escalation_payload)
            await producer.produce("escalations", json.dumps(escalation_payload))

if __name__ == "__main__":
    asyncio.run(run_escalation())
