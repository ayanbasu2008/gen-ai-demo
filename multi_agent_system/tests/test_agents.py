"""
Production-grade test suite for the multi-agent system.
Run with: pytest tests/ -v
"""

import asyncio
import json
import pytest
from services.nlp_model import classify_request
from common.schemas import Request
from common.utils import safe_json_loads, safe_json_dumps
from common.processors import BillingProcessor, TechProcessor, GeneralProcessor
from common.settings import settings


# ============================================================================
# Classification Tests
# ============================================================================

@pytest.mark.asyncio
async def test_classify_request_billing():
    """Test billing request classification."""
    text = "Customer has an invoice issue"
    category = classify_request(text)
    assert category == "billing"


@pytest.mark.asyncio
async def test_classify_request_tech():
    """Test technical request classification."""
    text = "System error occurred"
    category = classify_request(text)
    assert category == "tech"


@pytest.mark.asyncio
async def test_classify_request_general():
    """Test general request classification."""
    text = "Need help with account"
    category = classify_request(text)
    assert category == "general"


# ============================================================================
# Utility Tests
# ============================================================================

def test_safe_json_loads_valid():
    """Test JSON parsing with valid input."""
    data = '{"id":"1","source":"chat","content":"Hello","timestamp":"2026-05-12T22:30:00"}'
    parsed = safe_json_loads(data)
    assert parsed["id"] == "1"
    assert parsed["source"] == "chat"


def test_safe_json_loads_invalid():
    """Test JSON parsing with invalid input."""
    data = '{"id":1, "source": "chat" '  # malformed JSON
    parsed = safe_json_loads(data)
    assert parsed == {}


def test_safe_json_dumps_valid():
    """Test JSON serialization."""
    obj = {"id": "2", "status": "success"}
    dumped = safe_json_dumps(obj)
    assert isinstance(dumped, str)
    assert '"status": "success"' in dumped


# ============================================================================
# Schema Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_request_schema_serialization():
    """Test request schema serialization and deserialization."""
    req = Request(
        id="3",
        source="email",
        content="Bug report",
        timestamp="2026-05-12T22:31:00"
    )
    json_str = req.model_dump_json()
    parsed = Request.model_validate_json(json_str)
    assert parsed.id == "3"
    assert parsed.content == "Bug report"


# ============================================================================
# Billing Processor Tests
# ============================================================================

class TestBillingProcessor:
    """Test billing request processor."""
    
    def test_urgent_billing_request(self):
        """Test urgent billing request handling."""
        request_data = {
            "id": "BILL-001",
            "source": "email",
            "content": "URGENT: Invoice amount is incorrect",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = BillingProcessor.process(request_data)
        
        assert response["status"] == "escalated"
        assert response["priority"] == "high"
        assert response["request_id"] == "BILL-001"
        assert "Escalating" in response["details"]
    
    def test_refund_billing_request(self):
        """Test refund billing request handling."""
        request_data = {
            "id": "BILL-002",
            "source": "email",
            "content": "Please process my refund request",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = BillingProcessor.process(request_data)
        
        assert response["status"] == "processing"
        assert response["priority"] == "medium"
        assert "Refund request" in response["details"]
    
    def test_invoice_billing_request(self):
        """Test invoice billing request handling."""
        request_data = {
            "id": "BILL-003",
            "source": "email",
            "content": "The invoice has wrong amount",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = BillingProcessor.process(request_data)
        
        assert response["status"] == "resolved"
        assert response["priority"] == "low"
        assert "corrected" in response["details"]
    
    def test_generic_billing_request(self):
        """Test generic billing request handling."""
        request_data = {
            "id": "BILL-004",
            "source": "email",
            "content": "I have a question about my account",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = BillingProcessor.process(request_data)
        
        assert response["status"] == "in_progress"
        assert response["priority"] == "medium"
        assert "billing team" in response["details"]
    
    def test_billing_response_structure(self):
        """Test billing processor response structure."""
        request_data = {
            "id": "BILL-005",
            "source": "email",
            "content": "Test invoice",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = BillingProcessor.process(request_data)
        
        # Check required fields
        assert "status" in response
        assert "details" in response
        assert "priority" in response
        assert "request_id" in response
        assert "processed_at" in response
        assert "processor" in response
        assert response["processor"] == "BillingProcessor"


# ============================================================================
# Technical Processor Tests
# ============================================================================

class TestTechProcessor:
    """Test technical request processor."""
    
    def test_outage_tech_request(self):
        """Test system outage handling."""
        request_data = {
            "id": "TECH-001",
            "source": "ticket",
            "content": "System is down, complete outage",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = TechProcessor.process(request_data)
        
        assert response["status"] == "critical"
        assert response["priority"] == "critical"
        assert "outage" in response["details"]
    
    def test_performance_tech_request(self):
        """Test performance issue handling."""
        request_data = {
            "id": "TECH-002",
            "source": "ticket",
            "content": "Application is running very slow",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = TechProcessor.process(request_data)
        
        assert response["status"] == "investigating"
        assert response["priority"] == "high"
        assert "Performance" in response["details"]
    
    def test_database_error_tech_request(self):
        """Test database error handling."""
        request_data = {
            "id": "TECH-003",
            "source": "ticket",
            "content": "Database connection error occurring",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = TechProcessor.process(request_data)
        
        assert response["status"] == "debugging"
        assert response["priority"] == "high"
        assert "engineer" in response["details"]
    
    def test_generic_tech_request(self):
        """Test generic technical request."""
        request_data = {
            "id": "TECH-004",
            "source": "ticket",
            "content": "Can you help with general IT support",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = TechProcessor.process(request_data)
        
        assert response["status"] == "resolved"
        assert response["priority"] == "medium"


# ============================================================================
# General Processor Tests
# ============================================================================

class TestGeneralProcessor:
    """Test general request processor."""
    
    def test_general_request(self):
        """Test general request processing."""
        request_data = {
            "id": "GEN-001",
            "source": "phone",
            "content": "I have a general question",
            "timestamp": "2026-05-13T12:00:00",
        }
        response = GeneralProcessor.process(request_data)
        
        assert response["status"] == "received"
        assert response["priority"] == "low"
        assert "queued" in response["details"]


# ============================================================================
# Settings Tests
# ============================================================================

def test_settings_loaded():
    """Test that settings are properly loaded."""
    assert settings is not None
    assert settings.KAFKA_BOOTSTRAP is not None
    assert settings.JWT_SECRET is not None
    assert settings.API_KEY is not None
    assert settings.LOG_LEVEL is not None


def test_settings_environment():
    """Test that environment variable is set."""
    assert settings.ENVIRONMENT is not None
    assert settings.ENVIRONMENT in ["development", "production"]


def test_settings_retry_config():
    """Test retry configuration."""
    assert settings.KAFKA_RETRY_MAX_ATTEMPTS > 0
    assert settings.KAFKA_RETRY_DELAY_SECONDS > 0
