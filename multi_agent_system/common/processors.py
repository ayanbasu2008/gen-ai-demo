"""
Dynamic agent processor for handling business logic.
This module provides utilities to generate agent responses based on request content.
"""

import json
from typing import Dict, Any
from datetime import datetime
from common.logger import get_logger

logger = get_logger(__name__)


class BillingProcessor:
    """Process billing-related requests with dynamic logic."""
    
    @staticmethod
    def process(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process billing request and generate dynamic response."""
        try:
            content = request_data.get("content", "").lower()
            request_id = request_data.get("id", "unknown")
            
            # Dynamic response based on content
            if "urgent" in content or "critical" in content:
                status = "escalated"
                details = f"Urgent billing issue detected for {request_id}. Escalating to senior billing team."
                priority = "high"
            elif "refund" in content:
                status = "processing"
                details = f"Refund request {request_id} is being processed. Expected completion in 5-7 business days."
                priority = "medium"
            elif "invoice" in content:
                status = "resolved"
                details = f"Invoice discrepancy for {request_id} has been reviewed and corrected."
                priority = "low"
            else:
                status = "in_progress"
                details = f"Billing issue {request_id} is under review by our billing team."
                priority = "medium"
            
            return {
                "status": status,
                "details": details,
                "priority": priority,
                "request_id": request_id,
                "processed_at": datetime.utcnow().isoformat(),
                "processor": "BillingProcessor",
            }
        except Exception as e:
            logger.error("Error processing billing request", error=str(e))
            return {
                "status": "error",
                "details": f"Error processing billing request: {str(e)}",
                "priority": "critical",
            }


class TechProcessor:
    """Process technical-related requests with dynamic logic."""
    
    @staticmethod
    def process(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process tech request and generate dynamic response."""
        try:
            content = request_data.get("content", "").lower()
            request_id = request_data.get("id", "unknown")
            
            # Dynamic response based on content
            if "down" in content or "outage" in content:
                status = "critical"
                details = f"System outage detected for {request_id}. Incident response team engaged."
                priority = "critical"
            elif "performance" in content or "slow" in content:
                status = "investigating"
                details = f"Performance issue {request_id} is being investigated. Monitoring in progress."
                priority = "high"
            elif "database" in content or "error" in content:
                status = "debugging"
                details = f"Technical error {request_id} logged and engineer assigned for debugging."
                priority = "high"
            else:
                status = "resolved"
                details = f"Technical issue {request_id} has been resolved."
                priority = "medium"
            
            return {
                "status": status,
                "details": details,
                "priority": priority,
                "request_id": request_id,
                "processed_at": datetime.utcnow().isoformat(),
                "processor": "TechProcessor",
            }
        except Exception as e:
            logger.error("Error processing tech request", error=str(e))
            return {
                "status": "error",
                "details": f"Error processing tech request: {str(e)}",
                "priority": "critical",
            }


class GeneralProcessor:
    """Process general requests with dynamic logic."""
    
    @staticmethod
    def process(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process general request and generate dynamic response."""
        try:
            request_id = request_data.get("id", "unknown")
            
            return {
                "status": "received",
                "details": f"General request {request_id} received and queued for processing.",
                "priority": "low",
                "request_id": request_id,
                "processed_at": datetime.utcnow().isoformat(),
                "processor": "GeneralProcessor",
            }
        except Exception as e:
            logger.error("Error processing general request", error=str(e))
            return {
                "status": "error",
                "details": f"Error processing general request: {str(e)}",
                "priority": "critical",
            }


def get_processor(agent_type: str):
    """Get the appropriate processor for the agent type."""
    processors = {
        "billing": BillingProcessor,
        "tech": TechProcessor,
        "general": GeneralProcessor,
    }
    return processors.get(agent_type, GeneralProcessor)
