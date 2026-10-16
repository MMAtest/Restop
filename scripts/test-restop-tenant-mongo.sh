#!/usr/bin/env bash
# Fully ephemeral MongoDB replica-set QA: no exposed ports, volumes or client data.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="restop-tenant-qa-$(date +%s)-$$"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker info >/dev/null
printf '%s\n' "[RESTOP QA] Creating isolated MongoDB container: $name"
docker run -d --name "$name" mongo:7 --replSet rsrestopQA --bind_ip_all >/dev/null
# Use PyMongo to initiate the replica set. Avoid reliance on the mongosh binary,
# which may be broken in local/old cached Docker image layers.
docker run --rm --network "container:$name" \
  --mount "type=bind,source=${ROOT}/backend,target=/app,readonly" -w /app \
  -e 'RESTOP_TEST_TENANT_MONGO_URL=mongodb://localhost:27017/?directConnection=true&replicaSet=rsrestopQA' \
  python:3.11-slim sh -ec '
    pip -q install --disable-pip-version-check motor==3.3.1 pymongo==4.5.0 fastapi==0.110.1 pydantic==2.11.7 httpx==0.27.2
    python - <<"PY"
import time
from pymongo import MongoClient
url="mongodb://localhost:27017/?directConnection=true"
client=MongoClient(url,serverSelectionTimeoutMS=2000)
for retry in range(70):
    try:
        client.admin.command("ping")
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("MongoDB QA did not respond after 70 retries")
try:
    client.admin.command({"replSetInitiate":{"_id":"rsrestopQA","members":[{"_id":0,"host":"localhost:27017"}]}})
except Exception as exc:
    if "already initialized" not in str(exc).lower():
        raise
for retry in range(70):
    try:
        if client.admin.command("hello").get("isWritablePrimary"):
            print("[RESTOP QA] Isolated MongoDB primary ready")
            break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit("MongoDB QA replica set never became writable primary")
client.close()
PY
    python -m unittest test_tenant_mongo_integration test_tenant_workflows_mongo_integration -v
  '
printf '%s\n' '[RESTOP QA] PASS — isolated MongoDB and Python test container removed.'
