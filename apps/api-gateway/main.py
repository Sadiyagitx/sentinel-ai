"""
SentinelAI API Gateway — Production FastAPI Backend
====================================================
Handles: REST APIs, WebSocket broadcasting, Redis pub/sub, AI agent orchestration
"""

import os
import sys
import json
import uuid
import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis.asyncio as aioredis

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("sentinel.api")

# ─── Config ───────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── App Init ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SentinelAI API Gateway",
    description="AI-Powered Autonomous Observability Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── State ────────────────────────────────────────────────────────────────────
redis_client: Optional[aioredis.Redis] = None
active_ws: Set[WebSocket] = set()
incident_store: List[Dict[str, Any]] = []
telemetry_buffer: List[Dict[str, Any]] = []

# ─── Schemas ──────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    incident_id: str
    service: str
    summary: str
    severity: Optional[str] = "high"

class CreateIncidentRequest(BaseModel):
    service: str
    summary: str
    severity: str = "high"

# ─── Startup / Shutdown ───────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    global redis_client
    try:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        log.info("✅ Redis connected at %s", REDIS_URL)
        asyncio.create_task(redis_pubsub_listener())
    except Exception as e:
        log.warning("⚠️  Redis not available (%s). Running without pub/sub.", e)
        asyncio.create_task(mock_telemetry_generator())

    # Seed some historical incidents on boot
    _seed_incidents()
    log.info("🚀 SentinelAI API Gateway is ready.")

@app.on_event("shutdown")
async def on_shutdown():
    if redis_client:
        await redis_client.aclose()

# ─── Seed Data ────────────────────────────────────────────────────────────────
def _seed_incidents():
    seeds = [
        {"id": "inc_001", "severity": "critical", "service": "payments-api",      "summary": "P99 latency spiked to 4.2s following v2.3.1 rollout"},
        {"id": "inc_002", "severity": "high",     "service": "auth-service",       "summary": "JWT verification failure rate at 12% — Redis TTL misconfiguration"},
        {"id": "inc_003", "severity": "medium",   "service": "user-db",            "summary": "Connection pool exhausted: 512/512 connections active"},
    ]
    for s in seeds:
        s["ts"] = datetime.now(timezone.utc).isoformat()
        incident_store.append(s)

# ─── WebSocket Manager ────────────────────────────────────────────────────────
async def broadcast(data: dict):
    if not active_ws:
        return
    msg = json.dumps(data)
    dead: Set[WebSocket] = set()
    for ws in active_ws:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    active_ws.difference_update(dead)

# ─── Redis Pub/Sub Listener ───────────────────────────────────────────────────
async def redis_pubsub_listener():
    if not redis_client:
        return
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("sentinel_telemetry", "sentinel_incidents")
    log.info("📡 Subscribed to Redis channels")
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                await broadcast(data)
                if data.get("type") == "telemetry":
                    telemetry_buffer.append(data)
                    if len(telemetry_buffer) > 200:
                        telemetry_buffer.pop(0)
                elif data.get("type") == "incident":
                    data["ts"] = datetime.now(timezone.utc).isoformat()
                    incident_store.insert(0, data)
                    if len(incident_store) > 50:
                        incident_store.pop()
            except Exception as e:
                log.warning("Pub/sub parse error: %s", e)

# ─── Mock Telemetry (fallback when Redis unavailable) ─────────────────────────
async def mock_telemetry_generator():
    """Generates and broadcasts synthetic telemetry when Redis is not available."""
    log.info("🔄 Mock telemetry generator started (Redis fallback mode)")
    services = ["payments-api", "auth-service", "user-db", "frontend", "notification-svc"]
    while True:
        telemetry = {
            "type": "telemetry",
            "latency": random.randint(10, 900),
            "cpu": random.randint(15, 97),
            "errors": random.randint(0, 280),
            "memory": random.randint(35, 94),
            "rps": random.randint(100, 5000),
            "service": random.choice(services),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        await broadcast(telemetry)
        telemetry_buffer.append(telemetry)
        if len(telemetry_buffer) > 200:
            telemetry_buffer.pop(0)

        # Randomly inject an incident (~4% chance per tick)
        if random.random() < 0.04:
            incident = {
                "type": "incident",
                "id": f"inc_{uuid.uuid4().hex[:6]}",
                "severity": random.choice(["critical", "critical", "high", "medium"]),
                "service": random.choice(services),
                "summary": random.choice([
                    "P99 latency threshold breached — deployment regression suspected",
                    "Error rate crossed 5% SLA threshold",
                    "Memory pressure detected — OOM risk in 10 minutes",
                    "DB connection pool exhausted: 512/512 active connections",
                    "Circuit breaker OPEN on downstream dependency",
                ]),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            await broadcast(incident)
            incident_store.insert(0, incident)
            if len(incident_store) > 50:
                incident_store.pop()

        await asyncio.sleep(1)

# ─── REST Endpoints ───────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    redis_ok = False
    if redis_client:
        try:
            redis_ok = await redis_client.ping()
        except Exception:
            pass
    return {
        "status": "healthy",
        "version": "1.0.0",
        "redis": "connected" if redis_ok else "unavailable (mock mode)",
        "active_ws_clients": len(active_ws),
        "incidents_tracked": len(incident_store),
        "ts": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/incidents", tags=["Incidents"])
async def get_incidents(limit: int = 20, severity: Optional[str] = None):
    data = incident_store
    if severity:
        data = [i for i in data if i.get("severity") == severity]
    return data[:limit]

@app.post("/incidents", tags=["Incidents"])
async def create_incident(req: CreateIncidentRequest):
    incident = {
        "id": f"inc_{uuid.uuid4().hex[:6]}",
        "type": "incident",
        "severity": req.severity,
        "service": req.service,
        "summary": req.summary,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    incident_store.insert(0, incident)
    await broadcast(incident)
    return incident

@app.get("/telemetry/history", tags=["Telemetry"])
async def telemetry_history(limit: int = 60):
    return telemetry_buffer[-limit:]

@app.get("/services", tags=["Services"])
async def list_services():
    return [
        {"name": "payments-api",      "status": "degraded",  "health": 68, "region": "us-east-1"},
        {"name": "auth-service",       "status": "healthy",   "health": 97, "region": "us-east-1"},
        {"name": "user-db",            "status": "warning",   "health": 74, "region": "us-east-1"},
        {"name": "frontend",           "status": "healthy",   "health": 99, "region": "global-cdn"},
        {"name": "notification-svc",   "status": "healthy",   "health": 95, "region": "us-west-2"},
    ]

@app.post("/analyze", tags=["AI Agent"])
async def analyze_incident(req: AnalyzeRequest):
    """
    Run the SentinelAI Root Cause Agent on a given incident.
    Falls back to a rich deterministic response when OpenAI is not configured.
    """
    try:
        # Try importing the real LangGraph agent
        agent_path = os.path.join(os.path.dirname(__file__), "..", "..", "ai-agents")
        if agent_path not in sys.path:
            sys.path.insert(0, agent_path)
        from rootcause_agent import analyze
        result = await analyze({
            "incident": req.model_dump(),
            "openai_key": OPENAI_API_KEY,
        })
        return result
    except Exception as e:
        log.warning("AI agent exception (%s) — using deterministic fallback.", e)
        return _deterministic_analysis(req)

def _deterministic_analysis(req: AnalyzeRequest) -> dict:
    """Rich fallback analysis when the LLM is unavailable."""
    playbooks: Dict[str, dict] = {
        "payments-api": {
            "root_cause": "Deployment regression in v2.3.1 introduced a synchronous DB call inside an async handler, causing thread starvation under high load. Redis connection pool limits are also saturated.",
            "confidence": 0.94,
            "actions": [
                "Rollback payments-api to v2.2.9 immediately",
                "Scale Redis connection pool from 128 → 512",
                "Add circuit breaker around DB calls in PaymentProcessor",
                "Enable read-replica routing for non-critical queries",
            ],
            "severity": "critical",
        },
        "auth-service": {
            "root_cause": "JWT verification is calling Redis on every request for token blacklisting, but Redis TTL was set to 0 during a misconfigured deploy, causing all lookups to miss and fall back to the DB.",
            "confidence": 0.91,
            "actions": [
                "Fix Redis TTL configuration in auth-service ConfigMap",
                "Add local in-memory cache (LRU) as L1 before Redis",
                "Set up Redis Sentinel for HA failover",
                "Alert on Redis miss-rate > 5%",
            ],
            "severity": "high",
        },
        "user-db": {
            "root_cause": "PgBouncer connection pool exhausted due to long-running analytical queries blocking OLTP traffic. N+1 query pattern detected in the user profile endpoint.",
            "confidence": 0.89,
            "actions": [
                "Terminate long-running queries older than 30s",
                "Move analytical queries to read replica",
                "Fix N+1 query in UserProfileService.getById()",
                "Increase PgBouncer pool_size to 200",
            ],
            "severity": "high",
        },
    }
    default = {
        "root_cause": f"Anomalous behavior detected in {req.service}. Probable cause: upstream dependency degradation or recent configuration drift triggering cascading failures.",
        "confidence": 0.85,
        "actions": [
            f"Check {req.service} recent deployment history",
            "Inspect upstream service health metrics",
            "Review rate-limiter and circuit breaker configurations",
            "Scale horizontal replicas to absorb load",
        ],
        "severity": req.severity,
    }
    result = playbooks.get(req.service, default)
    return {
        "incident_id": req.incident_id,
        "service": req.service,
        **result,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "agent": "SentinelAI RootCause Agent v1.0",
    }

# ─── WebSocket Endpoint ───────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_ws.add(websocket)
    client = websocket.client
    log.info("🔌 WebSocket connected: %s:%s (total: %d)", client.host, client.port, len(active_ws))

    # Send snapshot of recent telemetry + incidents on connect
    await websocket.send_text(json.dumps({
        "type": "snapshot",
        "incidents": incident_store[:5],
        "telemetry": telemetry_buffer[-10:],
    }))

    try:
        while True:
            await asyncio.sleep(30)  # Keep-alive ping
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        active_ws.discard(websocket)
        log.info("🔌 WebSocket disconnected. Remaining: %d", len(active_ws))
    except Exception as e:
        active_ws.discard(websocket)
        log.warning("WebSocket error: %s", e)
