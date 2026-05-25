# SentinelAI

AI-Powered Autonomous Incident Root Cause Analyzer

---

## Overview

SentinelAI is an AI-native observability platform designed for modern distributed systems and cloud-native infrastructure.

The platform continuously ingests:

* logs
* metrics
* traces
* deployment events
* telemetry streams
* service health signals

Then autonomously:

* detects anomalies
* correlates incidents
* identifies root causes
* predicts blast radius
* recommends remediations
* generates incident summaries
* streams live operational intelligence

SentinelAI combines the capabilities of:

* Datadog
* Grafana Cloud
* PagerDuty
* Linear
* Vercel

into a single autonomous AI operations platform.

---

# Core Features

## Real-Time Observability

* Live telemetry dashboards
* Streaming metrics
* WebSocket-powered updates
* Service dependency monitoring
* Distributed tracing visualization
* Deployment tracking

---

## AI Incident Intelligence

### Multi-Agent AI System

SentinelAI includes specialized AI agents:

| Agent                       | Responsibility                      |
| --------------------------- | ----------------------------------- |
| Log Analysis Agent          | Detects anomalous log patterns      |
| Metrics Correlation Agent   | Correlates spikes across services   |
| Root Cause Agent            | Identifies probable failure sources |
| Remediation Agent           | Suggests fixes and rollback actions |
| Blast Radius Agent          | Predicts downstream service impact  |
| Deployment Regression Agent | Detects release-induced incidents   |
| Similar Incident Agent      | Retrieves historical incidents      |
| Incident Summary Agent      | Generates executive summaries       |

---

## Autonomous Operations

* AI root cause analysis
* AI rollback recommendations
* Incident replay engine
* Natural language infrastructure queries
* Semantic incident search
* Autonomous postmortem generation

---

# Architecture

```text
                    ┌─────────────────────┐
                    │     Frontend UI     │
                    │  Next.js + React    │
                    └─────────┬───────────┘
                              │
                     WebSockets / REST
                              │
                    ┌─────────▼──────────┐
                    │    FastAPI API     │
                    │  Gateway + Auth    │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
 ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
 │ Redis Streams  │ │ PostgreSQL DB  │ │ AI Agent Layer │
 └────────────────┘ └────────────────┘ └────────────────┘
          │                   │                   │
          └────────────┬──────┴────────────┬─────┘
                       ▼                   ▼
             ┌─────────────────┐ ┌─────────────────┐
             │ Telemetry Engine│ │ LangGraph AI    │
             └─────────────────┘ └─────────────────┘
```

---

# Tech Stack

## Frontend

* Next.js 15
* React 19
* TypeScript
* TailwindCSS
* shadcn/ui
* Framer Motion
* Zustand
* Recharts
* ReactFlow

---

## Backend

* FastAPI
* PostgreSQL
* Redis
* SQLAlchemy
* Alembic
* WebSockets
* Celery
* OpenTelemetry

---

## AI System

* LangGraph
* OpenAI-compatible models
* pgvector
* Embeddings
* RAG pipelines
* Semantic retrieval

---

## Infrastructure

* Docker
* Docker Compose
* Kubernetes
* Prometheus
* Grafana

---

# Monorepo Structure

```bash
sentinel-ai/
├── apps/
│   ├── web/
│   ├── api-gateway/
│   └── simulator/
│
├── ai-agents/
├── infra/
├── services/
├── packages/
├── shared/
├── scripts/
│
├── docker-compose.yml
├── turbo.json
└── README.md
```

---

# Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/your-org/sentinel-ai.git

cd sentinel-ai
```

---

## 2. Start Infrastructure

```bash
docker-compose up --build
```

---

# Service Ports

| Service            | Port |
| ------------------ | ---- |
| Frontend Dashboard | 3000 |
| FastAPI API        | 8000 |
| PostgreSQL         | 5432 |
| Redis              | 6379 |
| Grafana            | 3001 |
| Prometheus         | 9090 |

---

# Frontend

Frontend runs on:

```bash
http://localhost:3000
```

Features include:

* Live telemetry
* AI insights panel
* Incident center
* Deployment timeline
* Real-time alerts
* Service dependency graph

---

# Backend APIs

## Health Check

```http
GET /health
```

---

## List Incidents

```http
GET /incidents
```

---

## Create Incident

```http
POST /incidents
```

---

## WebSocket Stream

```text
ws://localhost:8000/ws
```

Streams:

* telemetry
* logs
* incidents
* traces
* AI analysis results

---

# AI Workflow

The AI orchestration layer uses LangGraph to coordinate specialized agents.

## Workflow

```text
Logs → Metrics → Correlation → Root Cause → Blast Radius → Remediation
```

Each AI execution produces:

* confidence score
* probable root cause
* impacted services
* remediation suggestions
* rollback analysis
* incident summary

---

# Live Incident Simulator

The simulator generates realistic infrastructure failures including:

* Kubernetes crashes
* API latency spikes
* Redis saturation
* DB deadlocks
* memory leaks
* cascading outages
* deployment regressions

Telemetry streams live through WebSockets.

---

# Deployment

## Docker

```bash
docker-compose up --build
```

---

## Kubernetes

```bash
kubectl apply -f infra/k8s/
```

---

# Environment Variables

## Backend

```env
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@postgres/sentinel
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=your_api_key
JWT_SECRET=super_secret
```

---

## Frontend

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

# Observability Stack

## Prometheus

Metrics collection and scraping.

## Grafana

Advanced telemetry visualization dashboards.

## OpenTelemetry

Distributed tracing and instrumentation.

---

# Demo Flow

## Recommended Demo Sequence

1. Open SentinelAI dashboard
2. Start telemetry simulator
3. Trigger deployment regression
4. Observe anomaly detection
5. Run AI root cause analysis
6. Watch blast radius prediction
7. Generate remediation suggestions
8. Display autonomous postmortem

---

# Scaling Strategy

## Future Enhancements

* Kafka ingestion pipelines
* Multi-region deployment
* GPU inference workers
* AI copilot for SRE teams
* Kubernetes operator
* Temporal workflow orchestration
* Edge telemetry ingestion
* Multi-tenant SaaS support

---

# Judge Pitch

SentinelAI transforms observability from passive monitoring into autonomous operational intelligence.

Instead of engineers manually debugging incidents:

SentinelAI:

* detects failures,
* correlates anomalies,
* identifies root causes,
* predicts impact,
* and recommends remediation automatically.

This is AI-native Site Reliability Engineering.

---

# License

MIT License

---

# Built For

* AI Infrastructure
* SRE Teams
* DevOps Platforms
* Cloud-Native Systems
* Distributed Architectures
* Real-Time Incident Intelligence
