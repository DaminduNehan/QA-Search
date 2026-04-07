#!/usr/bin/env sh
set -eu

echo "Starting deployment..."

if [ -z "${DEPLOY_API_TOKEN:-}" ]; then
  echo "DEPLOY_API_TOKEN is not set."
  exit 1
fi

if [ -z "${DEPLOY_WEBHOOK_URL:-}" ]; then
  echo "DEPLOY_WEBHOOK_URL is not set."
  echo "Add it as a repository secret to enable webhook deployment."
  exit 1
fi

curl -fsSL \
  -X POST \
  -H "Authorization: Bearer ${DEPLOY_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "${DEPLOY_WEBHOOK_URL}"

echo "Deployment webhook triggered successfully."
