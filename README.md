# OpenAI Integration Layer v3.0.0
## NDLOVU AI / ORA UNIVERSE — AI NATION v3.0

**Builder:** King Mandingu Letlape  
**Module:** F1 Part 4-5 — AI NATION v3.0 OpenAI Integration  
**Organization:** GLOBAL-LINK-DIGITAL-SOLUTIONS (The Crown)  
**CRYTONET Tier:** CRITICAL  
**Dharmakaya Guardian:** openai_bridge, openai_chat_endpoint, model_eval_registry, eval_dataset_builder

---

## 📋 Overview

This repository contains the **OpenAI Integration Layer** for the ORA Universe — four containerized microservices that handle:

1. **OpenAI Bridge (Container 21, Port 8021)** — HMAC-verified webhook receiver with Dharmakaya conscience gate
2. **OpenAI Chat Endpoint (Container 23, Port 8023)** — OpenAI-compatible /v1/chat/completions API with eval-driven model routing
3. **Model Eval Registry (Container 22, Port 8022)** — Performance scoring engine using ROUGE, BLEU, semantic similarity
4. **Eval Dataset Builder (Container 25, Port 8025)** — 14-entry sovereign benchmark suite generator
5. **WebSocket Server (Container 24, Port 8024)** — Real-time pub/sub dashboard (defined in docker-compose.merged.yml)

### Quick Architecture

```
OpenAI Webhooks ──▶ OpenAI Bridge (8021)
                         │
                    CRYTONET Layer
                    Dharmakaya Gate
                         │
                    ┌────┴─────┬──────────────┐
                    ▼          ▼              ▼
            Model Eval     Chat Endpoint   Dataset
            Registry       (8023)          Builder
            (8022)      /v1/compatible     (8025)
                           │
                    WebSocket (8024)
                    Pub/Sub Dashboard
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+
- Redis 7+
- OpenAI API Key

### Environment Setup

```bash
# Create .env file
cat > .env << EOF
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
OPENAI_API_KEY=<your-openai-key>
OPENAI_WEBHOOK_SECRET=<hmac-secret>
DHARMAKAYA_ENDPOINT=http://dharmakaya:8015
CRYTONET_ENDPOINT=http://crytonet:8028
MASTER_KERNEL_URL=http://master_kernel:8000
MODEL_EVAL_REGISTRY_URL=http://model_eval_registry:8022
EOF
```

### Local Development

```bash
pip install -r requirements.txt
python openai_bridge.py &
python openai_chat_endpoint.py &
python model_eval_registry.py &
python eval_dataset_builder.py
```

### Docker Deployment

```bash
# Build
docker build -t ndlovuai/openai-agents-python:v3.0.0 .

# Run with docker-compose
docker-compose -f docker-compose.merged.yml up -d
```

---

## 📚 Service Documentation

### 1. OpenAI Bridge (Port 8021)

**Receives OpenAI webhooks, verifies HMAC, passes Dharmakaya gate, routes to Master Kernel.**

```bash
# Receive webhook
POST /webhook
  Headers: X-Signature: sha256=<hmac>
  Body: { "event_type": "...", "model": "...", "messages": [...] }

# Health check
GET /health

# Metrics
GET /metrics
```

**Security Layers:**
- Layer 1: HMAC-SHA256 verification
- Layer 2: Dharmakaya conscience check
- Layer 3: Redis audit trail
- Layer 4: Master Kernel routing

---

### 2. OpenAI Chat Endpoint (Port 8023)

**OpenAI-compatible chat API with data-driven model routing.**

```bash
# Chat completion (OpenAI compatible)
POST /v1/chat/completions
  Body: {
    "model": "gpt-4-turbo",
    "messages": [{"role": "user", "content": "..."}],
    "temperature": 0.7,
    "max_tokens": 2048
  }

# Streaming
POST /v1/chat/completions/stream

# List models
GET /v1/models

# Model details
GET /v1/models/{model_id}

# Health
GET /health
```

**Response includes:**
- `model_routed`: Which model handled the request
- `crytonet_verified`: Security verification status
- `dharmakaya_approved`: Constitutional approval

---

### 3. Model Eval Registry (Port 8022)

**Aggregates model performance scores for intelligent routing.**

```bash
# Submit for evaluation
POST /api/v1/evals/submit
  Body: {
    "model": "gpt-4-turbo",
    "benchmark_entries": [...]
  }

# Get all scores
GET /api/v1/models/scores

# Get model scores
GET /api/v1/models/{model_id}/scores

# Get benchmarks
GET /api/v1/benchmarks

# Health
GET /health
```

**Scoring Metrics:**
- ROUGE-L: 0-1.0 (text similarity)
- BLEU: 0-1.0 (word precision)
- Semantic Similarity: 0-1.0 (embedding cosine)
- Quality Score: Composite (0-1.0)
- Efficiency: Latency + cost normalized
- Alignment: Dharmakaya constitutional (0-1.0)
- Composite: 50% quality + 30% efficiency + 20% alignment

---

### 4. Eval Dataset Builder (Port 8025)

**14-entry sovereign benchmark suite.**

**Domains:**
1. **Mandingu Governance** (7 entries)
   - Constitutional principles
   - DVE valuation
   - OTZA banking
   - NEARO foundation
   - CRYTONET layers
   - AI NATION routing
   - Memory network

2. **JobHub Recruitment** (6 entries)
   - Opportunity matching
   - Success-fee mechanics
   - Rules-based AI
   - EAC deployment
   - Phased launch
   - Financial projections

3. **African Legal** (1 entry)
   - B-BBEE compliance

```bash
# Get all benchmarks
GET /api/v1/benchmarks

# Get domain benchmarks
GET /api/v1/benchmarks/{domain}

# Get single entry
GET /api/v1/benchmarks/{domain}/{entry_number}

# Filter by difficulty
GET /api/v1/benchmarks/filter/difficulty?level=hard

# Export JSONL
GET /api/v1/benchmarks/export/jsonl

# Export CSV
GET /api/v1/benchmarks/export/csv

# Health
GET /health
```

---

## 🔐 Security & Governance

### CRYTONET (7-layer security)

1. **Quantum Shield** — Post-quantum cryptography
2. **Neural Firewall** — Pattern intrusion detection
3. **Behavioral Sentinel** — Anomaly ML
4. **Transaction Guardian** — Request validation
5. **Identity Fortress** — API key enforcement
6. **Compliance Oracle** — Regulatory checks
7. **Mandingu Shield** — Sovereign override

### Dharmakaya Integration

- **Constitutional checks** on all requests
- **Red Mode alerts** for violations
- **Alignment scoring** (0-1.0) for response quality
- **Multi-approval** for treasury/sensitive operations

### Rate Limiting

- Global: 10,000 req/min
- Per-user: 100 req/min
- Window: 60s (token bucket)

---

## 📊 Monitoring

### Health Checks

```json
GET /health
{
  "status": "healthy",
  "version": "3.0.0",
  "container": "openai_bridge",
  "redis_connected": true,
  "postgres_connected": true,
  "dharmakaya_status": "healthy",
  "crytonet_tier": "critical"
}
```

### Prometheus Metrics

```
GET /metrics
openai_bridge_total_events{...}
openai_bridge_approved_events{...}
openai_bridge_rejected_events{...}
```

### Logging

- **Format:** JSON with timestamps
- **Level:** INFO
- **Output:** stdout + crytonet_logs volume
- **Retention:** 90 days

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/ -v --cov

# Integration tests
docker-compose up -d
pytest tests/integration/ -v
docker-compose down

# Benchmark evaluation
curl -X POST http://localhost:8022/api/v1/evals/submit \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4-turbo", "benchmark_entries": [...]}'
```

---

## 🔧 Configuration

### openai_custom_provider_config.json

Defines 4 model configurations:

1. **openai_gpt4_turbo** — Critical reasoning (preferred)
2. **openai_gpt4** — Analysis (fallback)
3. **openai_gpt35_turbo** — Fast/cheap (cost-optimized)
4. **ndlovu_sovereign_ai** — Internal model (zero cost, Dharmakaya-aware)

**Routing Rules:**
- Governance → GPT-4 Turbo + Dharmakaya gate
- Recruitment → GPT-3.5 (fast) or Ndlovu (cheap)
- Legal → GPT-4 Turbo (reasoning)
- Analysis → GPT-4 (general)

---

## 📦 Deployment

### Docker Build

```bash
docker build -t ndlovuai/openai-agents-python:v3.0.0 .
docker push ghcr.io/GLOBAL-LINK-DIGITAL-SOLUTIONS/openai-agents-python:v3.0.0
```

### Docker Compose

See `docker-compose.merged.yml` for full 30-container ORA Universe deployment.

---

## 🎯 Integration Points

**Receives from:**
- Master Kernel (8000)
- OpenAI webhooks

**Sends to:**
- Dharmakaya (8015)
- CRYTONET (8028)
- Master Kernel (8000)
- WebSocket Server (8024)
- PostgreSQL (5432)
- Redis (6379)

---

## 📝 Code Structure

```
openai-agents-python/
├── openai_bridge.py
├── openai_chat_endpoint.py
├── model_eval_registry.py
├── eval_dataset_builder.py
├── openai_custom_provider_config.json
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🚦 API Quick Reference

| Service | Method | Endpoint | Purpose |
|---------|--------|----------|---------|
| Bridge | POST | `/webhook` | Receive webhooks |
| Chat | POST | `/v1/chat/completions` | Chat API |
| Chat | GET | `/v1/models` | List models |
| Eval | POST | `/api/v1/evals/submit` | Submit for eval |
| Eval | GET | `/api/v1/models/scores` | Get scores |
| Dataset | GET | `/api/v1/benchmarks` | Get benchmarks |

---

## 🔗 Next Steps

- **PRIORITY 3:** Real-Time Dashboard (React + WebSocket)
- **PRIORITY 4:** Master Kernel Router (eval-driven routing engine)
- **PRIORITY 5:** Axi-Africa Mirrors (4 community repositories)

---

## 📞 Support

- **Issues:** GitHub Issues
- **Email:** Otgoat@ndlovuai.com
- **Phone:** 076 833 3937

---

## 📄 License

MIT License

---

## 🙏 Attribution

**Builder:** King Mandingu Letlape  
**Module:** F1 Part 4-5 — AI NATION v3.0  
**Organization:** GLOBAL-LINK-DIGITAL-SOLUTIONS  
**Version:** 3.0.0  
**Date:** 2026-08-29  
**Status:** Production Ready ✅

---

**END OF README.md**
