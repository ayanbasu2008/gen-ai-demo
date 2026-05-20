# Multi-Agent Support Platform

A production-grade multi-agent system for handling customer support workflows.  
This project demonstrates how independent agents can collaborate via Kafka, PostgreSQL, and FastAPI to classify, resolve, audit, and escalate customer requests.

---

## Features
- **Ingestion Agent**: Normalizes incoming requests from multiple channels.
- **Classification Agent**: Categorizes requests (billing, tech, general).
- **Resolution Agents**: Specialized agents for billing and technical issues.
- **Escalation Agent**: Flags unresolved cases and escalates to human support.
- **Audit Agent**: Logs all interactions for monitoring and compliance.
- **Monitoring Service**: Prometheus metrics for requests, latency, and errors.
- **API Gateway**: FastAPI server for external clients to submit requests.

---

## Architecture
- **Message Bus**: Kafka for agent-to-agent communication.
- **Database**: PostgreSQL for persistence of audit logs and escalations.
- **Monitoring**: Prometheus + Grafana for observability.
- **Deployment**: Docker Compose for local development, Kubernetes for production.

## Flow:
Client → API → Ingestion → Classification → Resolution → Audit → Escalation


---

## Repository Structure
multi-agent-support-platform/
├── agents/              # Individual agents
├── common/              # Shared schemas, config, utils
├── services/            # Kafka, DB, monitoring, NLP
├── api/                 # FastAPI server
├── tests/               # Pytest-based unit tests
├── docker-compose.yml   # Local stack (Kafka, Zookeeper, Postgres, API)
├── requirements.txt     # Python dependencies
└── README.md


---

## Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Install dependencies:
  ```bash
  pip install -r requirements.txt

## Run with Docker Compose
docker-compose up -d

This starts Kafka, Zookeeper, PostgreSQL, and the API service.

## Run Agents
python agents/ingestion_agent.py
python agents/classification_agent.py
python agents/billing_agent.py
python agents/tech_agent.py
python agents/audit_agent.py
python agents/escalation_agent.py

## Testing
pytest tests/test_agents.py -v

## Monitoring
python services/monitoring_service.py

Metrics available at: http://localhost:8001/metrics

## API Usage
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{"id":"123","source":"chat","content":"System error","timestamp":"2026-05-12T22:31:00"}'

## Notes
Easiest way to run is via Docker Compose (no need to install PostgreSQL manually).

For production, deploy on Kubernetes with persistent volumes and monitoring stack.

Extendable: add new agents for new domains without breaking existing ones.

