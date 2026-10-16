#!/usr/bin/env bash
# Reproducible destructive-safe QA: temporary isolated Mongo replica set,
# temporary Python container, random temporary test DB. NOT production data.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="restop-tenant-qa-$(date +%s)-$$"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker info >/dev/null
printf '%s\n' "[RESTOP QA] Starting isolated MongoDB: $name"
docker run -d --rm --name "$name" mongo:7 --replSet rsrestopQA --bind_ip_all >/dev/null
ready=0
for i in $(seq 1 35); do
 if docker exec "$name" mongosh --quiet --eval 'db.runCommand({ping:1}).ok' 2>/dev/null | grep -q '1'; then ready=1;break;fi
 sleep 1
done
if [[ $ready != 1 ]];then echo 'MongoDB did not start' >&2;exit 1;fi
docker exec "$name" mongosh --quiet --eval 'rs.initiate({_id:"rsrestopQA",members:[{_id:0,host:"localhost:27017"}]})' >/dev/null
ready=0
for i in $(seq 1 35); do
 if docker exec "$name" mongosh --quiet --eval 'rs.status().myState' 2>/dev/null | grep -q '^1$'; then ready=1;break;fi
 sleep 1
done
if [[ $ready != 1 ]];then echo 'MongoDB replica set did not become primary' >&2;exit 1;fi
printf '%s\n' '[RESTOP QA] Running real FastAPI + Mongo transaction/tenant tests; no existing database is touched'
docker run --rm --network "container:$name" \
  --mount "type=bind,source=${ROOT}/backend,target=/app,readonly" -w /app \
  -e 'RESTOP_TEST_TENANT_MONGO_URL=mongodb://localhost:27017/?directConnection=true&replicaSet=rsrestopQA' \
  python:3.11-slim sh -ec '
    pip -q install --disable-pip-version-check motor==3.3.1 pymongo==4.5.0 fastapi==0.110.1 pydantic==2.11.7 httpx==0.27.2
    python -m unittest test_tenant_mongo_integration -v
  '
printf '%s\n' '[RESTOP QA] Passed. QA container automatically removed on exit.'
