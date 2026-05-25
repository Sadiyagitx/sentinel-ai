"""
SentinelAI Root Cause Agent
============================
Autonomous LangGraph-powered incident analysis agent.
Falls back gracefully when OpenAI is not available.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict

log = logging.getLogger("sentinel.agent")

SYSTEM_PROMPT = """You are SentinelAI, an elite Site Reliability Engineering AI agent.

Your mission: Diagnose production incidents with extreme precision and provide actionable remediation steps.

When analyzing an incident you must:
1. Identify the ROOT CAUSE from signal patterns, not just symptoms
2. Assess blast radius and downstream impact
3. Provide a confidence score (0.0 - 1.0) based on evidence strength
4. Output prioritized, executable remediation actions
5. Flag any correlated anomalies that indicate a wider systemic issue

Always be decisive. Time is critical in production incidents.
"""

# Playbook of known incident patterns mapped to RCA + remediation
INCIDENT_PLAYBOOK = {
    "payments-api": {
        "root_cause": (
            "Deployment regression in v2.3.1 introduced a blocking synchronous DB call inside an "
            "async coroutine, causing thread-pool starvation under high concurrency. Compounded by "
            "Redis connection pool saturation (128/128 connections held by idle workers)."
        ),
        "confidence": 0.94,
        "actions": [
            "IMMEDIATE: Rollback payments-api → v2.2.9 via 'kubectl rollout undo deployment/payments-api'",
            "Scale Redis connection pool: max_connections 128 → 512 in redis.conf",
            "Wrap DB calls in asyncio.to_thread() to prevent event-loop blocking",
            "Enable PgBouncer transaction-mode pooling for read queries",
            "Alert: Add metric alert on redis.connected_clients > 100",
        ],
        "blast_radius": "HIGH — Affects all checkout flows, order creation, and subscription renewals.",
    },
    "auth-service": {
        "root_cause": (
            "JWT token blacklist lookups hitting Redis with TTL=0 due to a misconfigured ConfigMap "
            "applied during yesterday's maintenance window. Every request falls back to a full PostgreSQL "
            "scan, increasing latency 10x and causing auth timeouts downstream."
        ),
        "confidence": 0.91,
        "actions": [
            "Fix Redis TTL: SET sentinel:blacklist:ttl 3600 in Redis CLI",
            "Redeploy auth-service with corrected ConfigMap: 'kubectl apply -f k8s/auth-configmap.yaml'",
            "Add local LRU in-memory cache (size=10k) as L1 before Redis",
            "Set alert: redis_keyspace_misses_total rate > 50/s",
            "Validate fix: Monitor auth.latency_p99 drops below 200ms",
        ],
        "blast_radius": "CRITICAL — All services relying on JWT validation are affected.",
    },
    "user-db": {
        "root_cause": (
            "PgBouncer connection pool fully saturated (512/512) due to long-running OLAP queries "
            "blocking OLTP traffic. Root cause: a recent analytics feature query runs on the primary "
            "replica without a timeout, holding connections for 45-90 seconds per request."
        ),
        "confidence": 0.89,
        "actions": [
            "Terminate blocker: SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > '30s'",
            "Route analytics queries to read-replica endpoint immediately",
            "Add statement_timeout=5000 to all OLTP connection strings",
            "Increase PgBouncer pool_size: 512 → 1024 in pgbouncer.ini",
            "Fix N+1 in UserProfileService.getById() — add .select_related('preferences')",
        ],
        "blast_radius": "HIGH — User profile reads, preferences, and settings APIs returning 503.",
    },
    "frontend": {
        "root_cause": (
            "CDN cache invalidation storm triggered by a mass-deploy of new static assets. "
            "Origin servers overwhelmed with cache-MISS requests, causing 60-second timeout cascades."
        ),
        "confidence": 0.87,
        "actions": [
            "Purge and re-warm CDN cache: 'curl -X DELETE https://cdn.sentinel.ai/purge/all'",
            "Increase CDN origin shield capacity temporarily",
            "Set Cache-Control: max-age=86400 for immutable hashed assets",
            "Enable stale-while-revalidate: 3600 on API responses",
        ],
        "blast_radius": "MEDIUM — Dashboard loading slow for all users, SPA shell returning 504.",
    },
}

GENERIC_ANALYSIS = {
    "root_cause": (
        "Anomalous spike in error rates and latency correlated with a recent deployment or configuration change. "
        "Probable cascading failure from a saturated upstream dependency — connection pool or external API rate limit."
    ),
    "confidence": 0.82,
    "actions": [
        "Check recent deployment history: 'kubectl rollout history deployment/{service}'",
        "Inspect upstream dependency health dashboards",
        "Review rate-limiter and circuit breaker trip counts",
        "Scale horizontal pod replicas: 'kubectl scale deployment/{service} --replicas=6'",
        "Add distributed tracing spans to identify the slowest component",
    ],
    "blast_radius": "UNKNOWN — Requires further investigation to determine downstream impact.",
}


async def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main analysis entrypoint. 
    Attempts OpenAI LLM analysis, falls back to deterministic playbook.
    """
    incident = state.get("incident", {})
    service = incident.get("service", "unknown")
    summary = incident.get("summary", "")
    severity = incident.get("severity", "high")
    incident_id = incident.get("incident_id", "unknown")
    openai_key = state.get("openai_key", "")

    log.info("🤖 Analyzing incident %s for service: %s", incident_id, service)

    # Try real LLM analysis if key is available
    if openai_key and openai_key.startswith("sk-") and not openai_key.startswith("sk-mock"):
        try:
            result = await _llm_analyze(incident, openai_key)
            result["agent"] = "SentinelAI RootCause Agent v1.0 (LLM)"
            result["incident_id"] = incident_id
            return result
        except Exception as e:
            log.warning("LLM analysis failed (%s), using playbook fallback.", e)

    # Deterministic playbook fallback
    playbook = INCIDENT_PLAYBOOK.get(service, GENERIC_ANALYSIS)
    return {
        "incident_id": incident_id,
        "service": service,
        "severity": severity,
        "root_cause": playbook["root_cause"],
        "confidence": playbook["confidence"],
        "actions": [a.replace("{service}", service) for a in playbook["actions"]],
        "blast_radius": playbook.get("blast_radius", "Under investigation"),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "agent": "SentinelAI RootCause Agent v1.0 (Playbook)",
    }


async def _llm_analyze(incident: dict, api_key: str) -> dict:
    """Call OpenAI GPT-4o to perform root cause analysis."""
    import httpx

    prompt = f"""Analyze this production incident and provide root cause analysis:

Service: {incident.get('service')}
Severity: {incident.get('severity')}  
Summary: {incident.get('summary')}

Respond as JSON with keys: root_cause (string), confidence (float 0-1), actions (list of strings), blast_radius (string)
"""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        import json
        return json.loads(data["choices"][0]["message"]["content"])
