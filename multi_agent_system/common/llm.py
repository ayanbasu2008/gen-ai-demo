import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY environment variable not set. LLM features will fail gracefully.")

# Initialize OpenAI client (v1.0+ API)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def generate_summary_escalation(escalation_text, model="gpt-3.5-turbo"):
    """
    Generate a concise summary for an escalation case using OpenAI LLM.
    """
    if not client:
        logger.error("OpenAI client not initialized. OPENAI_API_KEY not set.")
        raise ValueError("OPENAI_API_KEY not configured.")
    
    try:
        prompt = f"Summarize the following escalation case in 2-3 sentences:\n{escalation_text}"
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating escalation summary: {e}")
        raise

def suggest_escalation_action(escalation_text, model="gpt-3.5-turbo"):
    """
    Suggest recommended actions for an escalation case using OpenAI LLM.
    """
    if not client:
        logger.error("OpenAI client not initialized. OPENAI_API_KEY not set.")
        raise ValueError("OPENAI_API_KEY not configured.")
    
    try:
        prompt = f"Given the following escalation case, suggest the most appropriate next action(s):\n{escalation_text}"
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error suggesting escalation action: {e}")
        raise
