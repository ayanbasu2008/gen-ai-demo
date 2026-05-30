# Technical Presentation + Live Demo Runbook

## 1) Presentation Goal (30 sec)
Show how this multi-agent platform processes support requests end-to-end using FastAPI + Kafka + PostgreSQL, and how observability plus LLM-enriched escalation (OpenAI) improve production readiness.

---

## 2) Suggested Talk Track (12-15 minutes)

### Slide 1: Problem Statement
- Enterprise support requests arrive from multiple channels.
- Single-service architectures become hard to scale and reason about.
- We need domain-specialized processing, isolation, and observability.

Speaker notes:
"This system decomposes support processing into specialized agents connected by Kafka."

### Slide 2: System Architecture
- API layer: FastAPI request intake.
- Event backbone: Kafka topics for decoupled communication.
- Processing layer: Classification, Billing, Tech, Audit, Escalation agents.
- AI layer: OpenAI-powered summarization and recommended actions during escalation.
- Persistence: PostgreSQL for audit and escalation records.
- Observability: Prometheus metrics and Grafana dashboards.

Speaker notes:
"Kafka gives us asynchronous, fault-tolerant handoff between agents."

### Slide 3: Topic-Driven Workflow
1. Client posts request to `/submit`.
2. API publishes to `classification_requests`.
3. Classification agent routes to `billing_requests` or `tech_requests` or `general_requests`.
4. Domain agent processes and publishes response to `audit_logs`.
5. Audit agent consumes logs; escalation agent watches for escalation signals.
6. For critical/escalated cases, escalation agent calls OpenAI to generate `summary` and `recommended_action`, then publishes to `escalations`.

Speaker notes:
"This is event choreography, not direct service-to-service coupling."

### Slide 4: API and Security
- `POST /submit`: secured by Bearer API key.
- `GET /health`: health endpoint.
- `GET /metrics`: Prometheus scrape endpoint.
- Request payload is validated through Pydantic schema.

Speaker notes:
"Security is enforced at API boundary before entering the event pipeline."

### Slide 5: Classification Logic
- Lightweight keyword classifier:
  - `invoice` -> billing
  - `error` / `bug` -> tech
  - otherwise -> general
- Fast and deterministic for demo and baseline production flow.

Speaker notes:
"Classifier is intentionally simple and replaceable with ML/NLP model later."

### Slide 6: Dynamic Domain Logic
- Billing processor detects urgency/refund/invoice and returns status + priority + details.
- Tech processor detects outage/performance/error and returns incident-oriented outcomes.
- Responses include `processed_at` and processor identity.
- Escalation agent enriches escalated events with LLM-generated summary and next-step recommendations.

Speaker notes:
"Processors demonstrate domain-specific reasoning with deterministic logic."

### Slide 7: Reliability and Resilience
- Kafka producer includes retry attempts + delay.
- Startup includes retry wrappers for topic creation and DB init.
- Agent runner supervises child processes and terminates all if one exits.

Speaker notes:
"Fail-fast supervision prevents partial, inconsistent processing states."

### Slide 8: Data and Auditability
- Migrations create `audit_logs` and `escalations` tables.
- Billing/Tech agents persist audit records.
- Escalation stream now carries AI-enriched fields (`summary`, `recommended_action`) for triage traceability.

Speaker notes:
"This allows post-mortem analysis and compliance reporting."

### Slide 9: Observability
- API metrics: request count and latency.
- Kafka metrics: produced/consumed message counters by topic.
- Agent metrics: processing duration and error counts.

Speaker notes:
"Dashboards let us validate throughput, latency, and failure trends in real time."

### Slide 10: Deployment Model
- Local: Docker Compose stack for Kafka, Postgres, API, Prometheus, Grafana.
- Production: Kubernetes manifests and health checks.

Speaker notes:
"The same architecture scales from laptop demo to cluster deployment."

### Slide 11: Known Gaps / Honest Engineering Notes
- `general_requests` topic is produced but there is no dedicated general agent process in `run_agents.py`.
- `/requests/{request_id}` references `get_audit_log`, which is not implemented in `DatabaseService`.
- API key defaults differ across docs and compose unless `.env` is set consistently.
- If `OPENAI_API_KEY` is missing/invalid, escalation still works but uses fallback placeholders for LLM fields.

Speaker notes:
"I am surfacing these intentionally as next hardening tasks."

### Slide 12: Roadmap
- Add General agent consumer and processing path.
- Implement request status lookup in DB service and API.
- Add dead-letter topic + idempotency key.
- Upgrade classifier to model-based intent detection.
- Add LLM observability metrics (call latency, failure rate, fallback count) and prompt/version governance.

Speaker notes:
"Current architecture is extensible; improvements are additive, not disruptive."

---

## 3) Live Demo Script (8-10 minutes) [ayan]

## Pre-demo setup
1. docker compose down -v   (if Docker Desktop is running, so remove volumes along with all containers)

## Pre-demo checklist (do this before audience joins)
1. Ensure Docker Desktop is running.
2. Ensure `.env` has:
   - `API_KEY=dev-api-key-change-in-production`
   - `KAFKA_BOOTSTRAP=localhost:29092`
  - `OPENAI_API_KEY=<your-openai-api-key>`
3. In project root, install Python deps once:

```powershell
pip install -r requirements.txt
```

## Demo Step A: Start infrastructure
```powershell
docker compose up -d
```

Verify:
```powershell
docker compose ps
```

## Demo Step B: Start agents
Open a terminal and run:
```powershell
python run_agents.py
```

Keep this terminal visible (shows agent logs).

## Demo Step C: Prove API health and auth
In second terminal:
```powershell
Invoke-RestMethod "http://localhost:8000/health"
```

Auth failure demo (optional):
```powershell
$badHeaders = @{
  Authorization = "Bearer wrong-key"
  "Content-Type" = "application/json"
}
$badBody = @{
  id = "AUTH-FAIL-1"
  source = "email"
  content = "invoice issue"
  timestamp = "2026-05-14T11:00:00"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/submit" -Method Post -Headers $badHeaders -Body $badBody
```

## Demo Step D: Send a billing request
```powershell
  $headers = @{
    Authorization = "Bearer dev-api-key-change-in-production"
    "Content-Type" = "application/json"
  }
  $billingBody = @{
    id = "DEMO-BILL-001"
    source = "email"
    content = "URGENT invoice issue"
    timestamp = "2026-05-28T18:35:00"
  } | ConvertTo-Json
  Invoke-RestMethod -Uri "http://localhost:8000/submit" -Method Post -Headers $headers -Body $billingBody
```

Expected talking point:
- Classification -> billing topic.
- Billing processor marks high priority/escalated or processing depending on content.
- Audit log entry appears.
- If escalated, escalation payload should include `summary` and `recommended_action`.

```powershell
  $headers = @{
    Authorization = "Bearer dev-api-key-change-in-production"
    "Content-Type" = "application/json"
  }
  $billingBody = @{
    id = "DEMO-BILL-001"
    source = "email"
    content = "Invoice discrepancy for last month statement. Please review and correct."
    timestamp = "2026-05-14T11:01:00"
  } | ConvertTo-Json
  Invoke-RestMethod -Uri "http://localhost:8000/submit" -Method Post -Headers $headers -Body $billingBody
```

## Demo Step E: Send a tech request
```powershell
  $headers = @{
    Authorization = "Bearer dev-api-key-change-in-production"
    "Content-Type" = "application/json"
  }
  $techBody = @{
    id = "DEMO-TECH-001"
    source = "ticket"
    content = "System outage and database error in production"
    timestamp = "2026-05-14T11:02:00"
  } | ConvertTo-Json
  Invoke-RestMethod -Uri "http://localhost:8000/submit" -Method Post -Headers $headers -Body $techBody
```

Expected talking point:
- Classification -> tech topic.
- Tech processor returns critical/debugging path.

```powershell
$headers = @{
  Authorization = "Bearer dev-api-key-change-in-production"
  "Content-Type" = "application/json"
  }
$techBody = @{
  id = "DEMO-TECH-NONESC-001"
  source = "ticket"
  content = "Application is slow during peak hours and performance needs investigation."
  timestamp = "2026-05-18T12:15:00"
  } | ConvertTo-Json

  Invoke-RestMethod -Uri "http://localhost:8000/submit" -Method Post -Headers $headers -Body $techBody
```
## Demo Step F: Show metrics endpoint
```powershell
Invoke-WebRequest "http://localhost:8000/metrics" -UseBasicParsing
```

Call out:
- `api_requests_total`
- `kafka_messages_produced_total`
- `kafka_messages_consumed_total`
- `agent_processing_duration_seconds`

## Demo Step G: Show dashboards
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/So***@5****3)

Show:
- request throughput,
- agent latency,
- topic activity.
- escalation activity and any spikes during urgent/critical inputs.

Prometheus quick flow (to avoid a blank graph view):
1. Open `http://localhost:9090/targets` and confirm `prometheus`, `api`, and `kafka` targets are `UP`.
2. Open `http://localhost:9090/query`.
3. Run query `up` and click `Execute`.
4. Run query `api_requests_total` after submitting demo requests.
5. Run query `  ` to show topic activity.
6. Switch to `Graph` tab for visual trend lines.

## Demo Step H (optional): Kafka topic evidence
```powershell
docker compose exec kafka kafka-topics --bootstrap-server kafka:9092 --list
```

```powershell
docker compose exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic audit_logs --from-beginning --timeout-ms 5000
```

```powershell
docker compose exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic escalations --from-beginning --timeout-ms 5000
```

Validate in escalation payload:
- `summary` contains LLM-generated case summary.
- `recommended_action` contains LLM-generated recommended next steps.
- If OpenAI call fails, fallback values appear as `[LLM summary unavailable]` and `[LLM recommendation unavailable]`.

## Demo Step I (optional): DB evidence
```powershell
docker compose exec postgres psql -U agent -d agents -c "SELECT id, source, status, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 10;"
```

---

## 4) Q&A Cheat Sheet

Q: Why Kafka instead of direct HTTP between agents?
A: Decoupling, backpressure handling, replayability, independent scaling, and fault isolation.

Q: How do you prevent message loss?
A: Producer retries are implemented; next upgrade is DLQ + stricter delivery semantics.

Q: How do you track request lifecycle?
A: Kafka topic transitions + audit persistence in Postgres + Prometheus metrics.

Q: Where is LLM used in this architecture?
A: In the Escalation agent only, to enrich high-severity events with a concise summary and recommended next action before publishing to `escalations`.

Q: What is production hardening next?
A: General-agent completion, status endpoint fix, DLQ/idempotency, stronger classification model.

---

## 5) Two-minute backup demo (if time is cut)
1. `docker compose up -d`
2. `python run_agents.py`
3. POST one billing payload.
4. Show `/metrics` and one Grafana panel.
5. Close with architecture slide + roadmap.

---

## 6) Presenter Tips
- Keep one terminal pinned on `run_agents.py` logs.
- Keep one terminal for API calls.
- Keep browser tabs pre-opened for `/health`, `/metrics`, Prometheus, Grafana.
- If a call fails, narrate troubleshooting transparently (auth, env vars, container health).
- End by highlighting extensibility: adding agents does not break existing pipeline.
