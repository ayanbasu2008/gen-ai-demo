# Production-Ready Multi-Agent System

This is a fully production-hardened multi-agent system with dynamic logic, security, monitoring, and deployment automation.

## Features

### ✅ Dynamic Agent Logic
- **BillingProcessor**: Analyzes billing requests and generates context-aware responses
- **TechProcessor**: Handles technical issues with priority-based responses
- **GeneralProcessor**: Routes general inquiries

### ✅ Security
- **API Key Authentication**: Secure access control for all endpoints
- **JWT Token Support**: Optional JWT-based authentication for advanced use cases
- **Input Validation**: Pydantic-based request validation
- **Environment Secrets**: Secure configuration management

### ✅ Monitoring & Observability
- **Prometheus Metrics**: Export metrics from API and Kafka
- **Grafana Dashboards**: Visual monitoring of system health and performance
- **Structured Logging**: JSON logging for production environments
- **Health Checks**: Service health endpoints and Kubernetes probes

### ✅ Deployment Automation
- **Docker Compose**: Local development with full stack
- **Kubernetes Manifests**: Production-grade K8s deployment
- **CI/CD Pipeline**: GitHub Actions for build, test, and deploy
- **Auto-Scaling**: Horizontal Pod Autoscaling based on metrics

### ✅ Production Features
- **Retry Logic**: Configurable Kafka retry mechanism
- **Error Handling**: Comprehensive error logging and recovery
- **Database Persistence**: PostgreSQL with migrations
- **Graceful Shutdown**: Proper resource cleanup

## Quick Start

### Development (Local)

1. **Setup Environment**
```bash
cp .env.example .env
pip install -r requirements.txt
```

2. **Start Services**
```bash
docker compose up -d
```

3. **Run Agents**
```bash
python run_agents.py
```

4. **Submit a Request**
```bash
curl -X POST http://localhost:8000/submit \
  -H "Authorization: Bearer dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"id":"REQ-001","source":"email","content":"Invoice amount is incorrect","timestamp":"2026-05-13T12:00:00"}'
```

5. **Access Monitoring**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Metrics: http://localhost:8000/metrics

### Production (Kubernetes)

1. **Create Secrets**
```bash
kubectl create namespace agent-system
kubectl create secret generic app-secrets \
  --from-literal=POSTGRES_PASSWORD=secure-password \
  --from-literal=API_KEY=your-api-key \
  --from-literal=JWT_SECRET=your-jwt-secret \
  -n agent-system
```

2. **Deploy**
```bash
kubectl apply -f k8s/deployment.yaml
```

3. **Verify**
```bash
kubectl get pods -n agent-system
kubectl logs -n agent-system deployment/api
```

## Configuration

### Environment Variables
- `ENVIRONMENT`: Set to `production` for production deployments
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `LOG_FORMAT`: json or text
- `API_KEY`: Your API key for request submission
- `JWT_SECRET`: Secret for JWT token signing
- `POSTGRES_PASSWORD`: Database password
- `KAFKA_BOOTSTRAP`: Kafka bootstrap servers
- `KAFKA_RETRY_MAX_ATTEMPTS`: Number of retry attempts (default: 5)
- `KAFKA_RETRY_DELAY_SECONDS`: Delay between retries in seconds (default: 2)

### Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong API_KEY and JWT_SECRET
- [ ] Enable SASL/SSL for Kafka in production
- [ ] Use network policies to restrict access
- [ ] Enable HTTPS/TLS for API endpoints
- [ ] Regularly update dependencies
- [ ] Implement rate limiting for API endpoints
- [ ] Use secrets management (Vault, AWS Secrets Manager, etc.)

## API Endpoints

### Authentication
All endpoints require the `API_KEY` header:
```
Authorization: Bearer your-api-key
```

### Submit Request
```
POST /submit
Content-Type: application/json

{
  "id": "REQ-001",
  "source": "email|ticket|phone",
  "content": "Issue description",
  "timestamp": "2026-05-13T12:00:00"
}

Response:
{
  "status": "submitted",
  "id": "REQ-001",
  "message": "Request queued for processing"
}
```

### Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Metrics
```
GET /metrics

Response: Prometheus metrics in text format
```

## Agent Flow

1. **Classification Agent**: Routes requests to appropriate category
   - "invoice" → billing_requests
   - "error"/"bug" → tech_requests
   - else → general_requests

2. **Domain Agents** (Billing, Tech): Process requests with dynamic logic
   - Analyze content
   - Generate context-aware responses
   - Store results in database
   - Publish to audit_logs

3. **Audit Agent**: Consumes and logs all audit events
   - Structured logging
   - Metrics recording
   - Database persistence

4. **Escalation Agent**: Monitors for critical issues
   - Watches audit_logs for escalation triggers
   - Publishes to escalations topic

## Monitoring

### Key Metrics
- `api_requests_total`: Total API requests by method, endpoint, and status
- `api_request_duration_seconds`: Request processing time
- `kafka_messages_produced_total`: Messages produced to Kafka by topic
- `kafka_messages_consumed_total`: Messages consumed from Kafka by topic
- `agent_processing_duration_seconds`: Agent processing time
- `agent_errors_total`: Total errors in agents

### Grafana Dashboards
Dashboards are auto-provisioned at startup. Key dashboards:
- System Overview: Overall health and request rates
- Agent Performance: Processing times and error rates
- Kafka Metrics: Message throughput and lag
- Infrastructure: CPU, memory, and resource usage

## Testing

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest --cov=. tests/

# Run specific test
pytest tests/test_agents.py::test_billing_processor -v
```

## Deployment Strategies

### Blue-Green Deployment
1. Deploy new version to new environment
2. Run smoke tests
3. Switch traffic to new environment
4. Keep old environment as rollback

### Canary Deployment
1. Deploy new version to small percentage of traffic
2. Monitor metrics and errors
3. Gradually increase traffic percentage
4. Rollback if issues detected

### Rolling Deployment
1. Update replicas one by one
2. Old pods are terminated after new pods are ready
3. Automatic with Kubernetes

## Troubleshooting

### Agent not processing messages
1. Check agent logs: `docker compose logs billing_agent`
2. Verify Kafka connectivity: `docker compose exec kafka kafka-topics --bootstrap-server kafka:9092 --list`
3. Check if topic has messages: `docker compose exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic billing_requests --from-beginning`

### API returning 403
- Verify API_KEY is correct
- Check Authorization header format: `Authorization: Bearer your-key`

### Grafana shows no data
- Verify Prometheus scrape config in `monitoring/prometheus.yml`
- Check API metrics endpoint: `curl http://localhost:8000/metrics`

## License
MIT

## Support
For issues and feature requests, please open an issue in the repository.
