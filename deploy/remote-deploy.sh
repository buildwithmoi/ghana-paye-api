#!/usr/bin/env bash
# Runs ON THE SERVER. The deploy job pipes it over SSH:
#   ssh deploy@server 'bash -s' -- <image-tag> <commit-sha> < deploy/remote-deploy.sh
#
# 1. Pull the new image and restart the service.
# 2. Wait until /health reports the new commit.
# 3. If it never does, roll back to the image that was running before, and fail.
set -euo pipefail

NEW_TAG="$1"   # e.g. sha-1a2b3c4
NEW_SHA="$2"   # the full commit SHA the image was built from
APP_DIR=/opt/ghana-paye-api
HEALTH_URL=http://127.0.0.1:8000/health

cd "$APP_DIR"
PREV_TAG=$(cat .deployed-tag 2>/dev/null || true)

run_tag() {
  IMAGE_TAG="$1" docker compose pull --quiet
  IMAGE_TAG="$1" docker compose up -d
}

# Wait up to ~40s for /health to answer, and to report the given commit if one is given.
wait_healthy() {
  local want="${1:-}"
  for _ in $(seq 1 20); do
    if body=$(curl -fsS "$HEALTH_URL" 2>/dev/null) && [[ -z "$want" || "$body" == *"\"commit\":\"$want\""* ]]; then
      return 0
    fi
    sleep 2
  done
  return 1
}

echo "Deploying $NEW_TAG (currently running: ${PREV_TAG:-nothing yet})"
run_tag "$NEW_TAG"

if wait_healthy "$NEW_SHA"; then
  echo "$NEW_TAG" > .deployed-tag
  echo "OK: /health reports commit $NEW_SHA"
  exit 0
fi

echo "Health check failed for $NEW_TAG. Recent logs:" >&2
docker compose logs --tail 50 >&2 || true

if [[ -n "$PREV_TAG" ]]; then
  echo "Rolling back to $PREV_TAG" >&2
  run_tag "$PREV_TAG"
  wait_healthy && echo "Rollback to $PREV_TAG is healthy" >&2
fi
exit 1
