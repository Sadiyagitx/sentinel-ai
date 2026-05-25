# SentinelAI: Final Architecture & Demo Details

## 🚀 Final Architecture Summary
SentinelAI is an AI-powered autonomous observability platform designed to replicate the feel of Datadog + Grafana + Linear, integrated with an AI agent layer for root cause analysis.

### Tech Stack:
- **Frontend (Web)**: Next.js 15, React 19, Tailwind CSS, Recharts, Framer Motion. Uses WebSockets to consume live streaming telemetry.
- **Backend (API Gateway)**: FastAPI (Python 3.11), handles REST endpoints and broadcasting WebSocket streams to clients. Integrates LangGraph for autonomous root cause analysis.
- **Simulator (Engine)**: Python script that continuously generates rich telemetry data (CPU, memory, latency) and injects intermittent critical incidents into the pipeline.
- **Database / Cache**: PostgreSQL (pgvector) for persistence, Redis for pub/sub telemetry streaming.
- **AI Agents**: Custom LangGraph + LangChain implementation simulating AI agent operations.
- **Infrastructure**: Docker Compose handles orchestration, networking, and dependencies.

---

## 🔗 Working Service URLs
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API Gateway**: [http://localhost:8000](http://localhost:8000)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Live Telemetry Stream (WS)**: `ws://localhost:8000/ws`

---

## 🔑 Credentials
- **PostgreSQL**: User: `sentinel` | Password: `sentinel` | DB: `sentinel`
- **Redis**: No auth required (Local environment)
- **OpenAI API**: The system is pre-configured to handle mock execution, but you can inject your key via `OPENAI_API_KEY` environment variable.

---

## 🏃‍♂️ Startup & Deployment Commands

### Option A: Docker Compose (Recommended)
This runs the full stack including Redis and PostgreSQL.
```bash
docker compose up -d --build
```

### Option B: Local PowerShell Startup
If Docker is not available on the machine, you can run the services using the provided automated script:
```powershell
.\judge-demo.ps1
```

---

## 🎮 Demo Walkthrough

1. **Launch the Platform**: Run `.\judge-demo.ps1` or `docker compose up -d --build`.
2. **Open the Dashboard**: Navigate to `http://localhost:3000` in your browser.
3. **Observe the Live Telemetry**: Watch the dynamic Recharts graph update in real-time as the Python simulator streams CPU and Latency metrics over WebSockets.
4. **Wait for an Incident**: The simulator randomly generates high-severity incidents (e.g., Database Saturation, Authentication Failures).
5. **Trigger AI Root Cause Analysis**: Click the "AI Root Cause Analysis" button on any active incident in the sidebar.
6. **Review the AI Diagnosis**: The LangGraph agent will process the incident context and output a confidence-scored diagnosis along with recommended mitigation actions.

Enjoy the autonomous observability experience!
