import os
import json
import logging
from datetime import datetime
from typing import Any, Dict
from openai import OpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY environment variable not set. LLM features will fail gracefully.")

# Initialize OpenAI client (v1.0+ API)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _chat_completion(prompt: str, model: str | None = None, temperature: float = 0.2, max_tokens: int = 250) -> str:
    """Run a chat completion and return plain text content."""
    if not client:
        raise ValueError("OPENAI_API_KEY not configured.")

    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a customer-support operations assistant. "
                    "Return concise and production-safe output."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()


def _chat_json(prompt: str, model: str | None = None, max_tokens: int = 350) -> Dict[str, Any]:
    """Request JSON output from the model and parse it safely."""
    raw = _chat_completion(
        prompt=(
            prompt
            + "\n\nReturn ONLY valid JSON. Do not include markdown code fences."
        ),
        model=model,
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return json.loads(raw)


def _fallback_category(text: str) -> str:
    normalized = text.lower()
    billing_keywords = ("invoice", "billing", "refund", "payment", "charge")
    tech_keywords = ("error", "bug", "outage", "down", "database", "performance", "slow")
    if any(keyword in normalized for keyword in billing_keywords):
        return "billing"
    if any(keyword in normalized for keyword in tech_keywords):
        return "tech"
    return "general"


def ai_classify_request(request_payload: Dict[str, Any], model: str | None = None) -> str:
    """Classify a request into billing, tech, or general with LLM + fallback."""
    content = str(request_payload.get("content", ""))
    source = str(request_payload.get("source", "unknown"))

    try:
        result = _chat_json(
            prompt=(
                "Classify this customer-support request into one of: billing, tech, general.\n"
                f"source: {source}\n"
                f"content: {content}\n"
                "JSON schema: {\"category\":\"billing|tech|general\"}"
            ),
            model=model,
            max_tokens=80,
        )
        category = str(result.get("category", "")).strip().lower()
        if category in {"billing", "tech", "general"}:
            return category
    except Exception as exc:
        logger.warning("LLM classification failed, falling back to keyword rules: %s", exc)

    return _fallback_category(content)


def ai_process_domain_request(domain: str, request_data: Dict[str, Any], model: str | None = None) -> Dict[str, Any]:
    """Generate AI-driven triage output for billing/tech/general domains."""
    request_id = request_data.get("id", "unknown")
    source = request_data.get("source", "unknown")
    content = str(request_data.get("content", ""))

    try:
        result = _chat_json(
            prompt=(
                f"You are the {domain} support agent. Analyze the request and produce an operational response.\n"
                f"request_id: {request_id}\n"
                f"source: {source}\n"
                f"content: {content}\n\n"
                "Rules:\n"
                "- status must be one of: resolved, in_progress, investigating, processing, escalated, critical, debugging, received\n"
                "- priority must be one of: low, medium, high, critical\n"
                "- details must be <= 240 chars and action-oriented\n"
                "JSON schema: {\"status\": str, \"priority\": str, \"details\": str, \"attempts\": int}"
            ),
            model=model,
            max_tokens=220,
        )

        status = str(result.get("status", "in_progress")).strip().lower()
        priority = str(result.get("priority", "medium")).strip().lower()
        details = str(result.get("details", "Request reviewed by AI agent.")).strip()
        attempts = int(result.get("attempts", 1))

        if status not in {"resolved", "in_progress", "investigating", "processing", "escalated", "critical", "debugging", "received"}:
            status = "in_progress"
        if priority not in {"low", "medium", "high", "critical"}:
            priority = "medium"
        if attempts < 1:
            attempts = 1

        return {
            "status": status,
            "details": details,
            "priority": priority,
            "attempts": attempts,
            "request_id": request_id,
            "processed_at": datetime.utcnow().isoformat(),
            "processor": f"AI{domain.title()}Processor",
            "source": source,
            "content": content,
        }
    except Exception as exc:
        logger.warning("LLM domain processing failed for domain=%s, returning safe fallback: %s", domain, exc)
        return {
            "status": "in_progress",
            "details": f"{domain.title()} request {request_id} queued for specialist review.",
            "priority": "medium",
            "attempts": 1,
            "request_id": request_id,
            "processed_at": datetime.utcnow().isoformat(),
            "processor": f"AI{domain.title()}ProcessorFallback",
            "source": source,
            "content": content,
        }


def ai_audit_assessment(audit_payload: Dict[str, Any], model: str | None = None) -> Dict[str, Any]:
    """Generate an AI risk and escalation assessment for audit events."""
    print("Running AI audit assessment for payload:", audit_payload)
    try:
        result = _chat_json(
            prompt=(
                "   \n"
                f"event: {json.dumps(audit_payload, default=str)}\n\n"
                "JSON schema: {\"risk_level\":\"low|medium|high|critical\","
                "\"requires_escalation\": bool,"
                "\"attempts_hint\": int,"
                "\"rationale\": str}"
            ),
            model=model,
            max_tokens=180,
        )

        risk_level = str(result.get("risk_level", "medium")).strip().lower()
        if risk_level not in {"low", "medium", "high", "critical"}:
            risk_level = "medium"

        requires_escalation = bool(result.get("requires_escalation", False))
        attempts_hint = int(result.get("attempts_hint", 1))
        if attempts_hint < 1:
            attempts_hint = 1

        rationale = str(result.get("rationale", "AI assessment completed.")).strip()
        return {
            "risk_level": risk_level,
            "requires_escalation": requires_escalation,
            "attempts_hint": attempts_hint,
            "rationale": rationale,
        }
    except Exception as exc:
        logger.warning("LLM audit assessment failed, using fallback: %s", exc)
        status = str(audit_payload.get("status", "")).lower()
        attempts = int(audit_payload.get("attempts", 1) or 1)
        fallback_escalation = status in {"critical", "escalated", "unresolved"} or attempts >= 2
        return {
            "risk_level": "high" if fallback_escalation else "low",
            "requires_escalation": fallback_escalation,
            "attempts_hint": attempts,
            "rationale": "Fallback assessment based on status and attempts.",
        }


def ai_escalation_decision(audit_payload: Dict[str, Any], model: str | None = None) -> Dict[str, Any]:
    """Decide whether escalation is required and why."""
    assessment = ai_audit_assessment(audit_payload, model=model)

    status = str(audit_payload.get("status", "")).lower()
    priority = str(audit_payload.get("priority", "")).lower()
    attempts = int(audit_payload.get("attempts", 1) or 1)
    signal_text = " ".join(
        [
            str(audit_payload.get("details", "")),
            str(audit_payload.get("content", "")),
            str(audit_payload.get("issue", "")),
        ]
    ).lower()

    urgent_markers = (
        "urgent",
        "critical",
        "outage",
        "down",
        "sev1",
        "p1",
        "data loss",
        "security incident",
    )

    # Keep escalation behavior predictable: AI can recommend escalation, but only
    # messages with hard operational signals are allowed to trigger escalation.
    rule_trigger = (
        status in {"critical", "escalated", "unresolved"}
        or priority == "critical"
        or attempts >= 2
        or any(marker in signal_text for marker in urgent_markers)
    )

    ai_recommends_escalation = bool(assessment.get("requires_escalation", False))
    should_escalate = rule_trigger or (ai_recommends_escalation and status in {"critical", "escalated", "unresolved"})

    if rule_trigger:
        reason = "Deterministic escalation trigger matched (status/priority/attempts/urgent markers)."
    elif ai_recommends_escalation and not rule_trigger:
        reason = "AI suggested escalation but deterministic policy blocked non-critical case."
    else:
        reason = assessment.get("rationale", "AI escalation review complete.")

    return {
        "should_escalate": should_escalate,
        "reason": reason,
        "risk_level": assessment.get("risk_level", "medium"),
        "attempts": assessment.get("attempts_hint", attempts),
    }

def generate_summary_escalation(escalation_text, model=DEFAULT_MODEL):
    """
    Generate a concise summary for an escalation case using OpenAI LLM.
    """
    if not client:
        logger.warning("OpenAI client not initialized. Returning fallback escalation summary.")
        return "Summary unavailable. Escalation details require manual review."
    
    try:
        return _chat_completion(
            prompt=f"Summarize the following escalation case in 2-3 sentences:\n{escalation_text}",
            model=model,
            max_tokens=150,
            temperature=0.4,
        )
    except Exception as e:
        logger.error(f"Error generating escalation summary: {e}")
        return "Summary unavailable. Escalation details require manual review."

def suggest_escalation_action(escalation_text, model=DEFAULT_MODEL):
    """
    Suggest recommended actions for an escalation case using OpenAI LLM.
    """
    if not client:
        logger.warning("OpenAI client not initialized. Returning fallback escalation action.")
        return "Assign case to human support lead and continue live monitoring."
    
    try:
        return _chat_completion(
            prompt=f"Given the following escalation case, suggest the most appropriate next action(s):\n{escalation_text}",
            model=model,
            max_tokens=100,
            temperature=0.4,
        )
    except Exception as e:
        logger.error(f"Error suggesting escalation action: {e}")
        return "Assign case to human support lead and continue live monitoring."
