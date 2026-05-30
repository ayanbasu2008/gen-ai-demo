# Quick Testing Reference

## Installation

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov
```

## Run Tests

### Quick Start
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_agents.py::TestBillingProcessor -v
```

## Test Categories

### 1. Unit Tests (Fast)
```bash
pytest tests/test_agents.py -v -m "not integration"
```

### 2. Classification Tests
```bash
pytest tests/test_agents.py::test_classify_request_billing -v
pytest tests/test_agents.py::test_classify_request_tech -v
pytest tests/test_agents.py::test_classify_request_general -v
```

### 3. Processor Tests (Dynamic Logic)
```bash
# Billing processor
pytest tests/test_agents.py::TestBillingProcessor -v

# Tech processor
pytest tests/test_agents.py::TestTechProcessor -v

# General processor
pytest tests/test_agents.py::TestGeneralProcessor -v
```

### 4. Settings & Configuration
```bash
pytest tests/test_agents.py::test_settings_loaded -v
```

## API Testing

### Manual API Test
```bash
# Submit request
curl -X POST http://localhost:8000/submit \
  -H "Authorization: Bearer dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "TEST-001",
    "source": "email",
    "content": "Invoice is incorrect",
    "timestamp": "2026-05-13T12:00:00"
  }'

# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

## Integration Testing

### Kafka Flow
```bash
# List topics
docker compose exec kafka kafka-topics --bootstrap-server kafka:9092 --list

# Check classification_requests
docker compose exec kafka kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic classification_requests --from-beginning --timeout-ms 5000

# Check billing_requests
docker compose exec kafka kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic billing_requests --from-beginning --timeout-ms 5000

# Check audit_logs
docker compose exec kafka kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic audit_logs --from-beginning --timeout-ms 5000
```

## End-to-End Testing

```bash
# 1. Start services
docker compose up -d

# 2. Start agents
python run_agents.py

# 3. Submit request
curl -X POST http://localhost:8000/submit \
  -H "Authorization: Bearer dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "E2E-001",
    "source": "email",
    "content": "URGENT invoice issue",
    "timestamp": "2026-05-13T12:00:00"
  }'

# 4. Monitor
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
# Metrics: http://localhost:8000/metrics
```

## Test Results Interpretation

### Passing Tests
```
PASSED tests/test_agents.py::TestBillingProcessor::test_urgent_billing_request
```

### Failing Tests
```
FAILED tests/test_agents.py::TestBillingProcessor::test_invalid_test - AssertionError
```

### Coverage Report
```
Name                                              Stmts   Miss  Cover
-------------------------------------------------------------------
common/processors.py                               100      5    95%
common/security.py                                  45      3    93%
api/server.py                                      120     10    92%
TOTAL                                             500     20    96%
```

## Troubleshooting

### Tests Won't Run
```bash
# Check Python version (need 3.10+)
python --version

# Check dependencies
pip install -r requirements.txt

# Reinstall test tools
pip install --upgrade pytest pytest-asyncio pytest-cov
```

### Kafka Tests Fail
```bash
# Check if Docker is running
docker ps

# Start services
docker compose up -d

# Check service health
docker compose ps
```

### Import Errors
```bash
# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/multi_agent_system
pytest tests/
```

## Performance Benchmarks

### Expected Test Execution Times
- Unit tests: ~2-5 seconds
- Classification tests: ~1 second each
- Processor tests: ~0.1 seconds each
- Full suite: ~15-30 seconds

### Optimization
```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

## Recommended Workflow

1. **Before committing**:
   ```bash
   pytest tests/ -v
   ```

2. **After code changes**:
   ```bash
   pytest tests/test_agents.py::TestBillingProcessor -v
   ```

3. **Before pushing**:
   ```bash
   pytest tests/ --cov=. --cov-report=term-missing
   ```

4. **For CI/CD**:
   ```bash
   pytest tests/ -v --tb=short --cov=. --cov-report=xml
   ```

## Next Steps

1. Read `TESTING_GUIDE.md` for comprehensive testing documentation
2. Review test cases in `tests/test_agents.py`
3. Create API tests in `tests/test_api.py`
4. Set up CI/CD in `.github/workflows/ci-cd.yml`
