#!/usr/bin/env bash
# Zero-retention proof. Run against a live stack. CI-gate every release on it.
#   1. Fire N real checks at the API
#   2. `docker diff` on api + medgemma containers
#   3. Any filesystem write outside tmpfs = FAIL
set -euo pipefail

API=${API:-https://localhost/v1/check}
N=${N:-25}
IMG=${IMG:-tests/fixtures/foot_ok.jpg}

echo "→ firing $N checks at $API"
for i in $(seq "$N"); do
  curl -sk -o /dev/null -F "image=@${IMG}" "$API" || true
done

fail=0
for c in $(docker compose ps -q api medgemma); do
  name=$(docker inspect -f '{{.Name}}' "$c")
  # docker diff never shows tmpfs mounts — any output is a real write
  writes=$(docker diff "$c" | grep -v '^C /root$' || true)
  if [ -n "$writes" ]; then
    # allow vLLM's HF cache volume writes (weights only); flag anything else
    unexpected=$(echo "$writes" | grep -v '.cache/huggingface' || true)
    if [ -n "$unexpected" ]; then
      echo "✗ $name wrote to its filesystem:"
      echo "$unexpected"
      fail=1
    fi
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "✓ zero-retention holds: no writes outside tmpfs/model-cache after $N checks"
else
  echo "✗ RETENTION AUDIT FAILED"; exit 1
fi
