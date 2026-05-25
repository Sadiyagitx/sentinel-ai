import asyncio
import random
import os
import redis.asyncio as redis
import json

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

async def simulate():
    r = redis.from_url(redis_url)
    print(f"Simulator connected to Redis at {redis_url}")
    while True:
        telemetry = {
            "type": "telemetry",
            "latency": random.randint(10, 900),
            "cpu": random.randint(20, 98),
            "errors": random.randint(0, 300),
            "memory": random.randint(40, 99)
        }
        await r.publish("sentinel_telemetry", json.dumps(telemetry))
        
        # Simulate an incident occasionally
        if random.random() < 0.05:
            incident = {
                "type": "incident",
                "id": f"inc_{random.randint(100, 999)}",
                "severity": random.choice(["critical", "high", "medium"]),
                "service": random.choice(["payments-api", "auth-service", "user-db", "frontend"]),
                "summary": "Threshold exceeded for error rates and latency"
            }
            await r.publish("sentinel_incidents", json.dumps(incident))

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(simulate())
