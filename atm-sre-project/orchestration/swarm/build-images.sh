#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

services=(
  "auth:services/auth"
  "account:services/account"
  "transaction:services/transaction"
  "history:services/history"
  "card-management:services/card-management"
  "gateway:services/gateway"
  "background-load:services/background-load"
  "frontend:frontend"
)

echo "==> Building all ATM SRE images..."

for entry in "${services[@]}"; do
  name="${entry%%:*}"
  context="${entry##*:}"
  echo ""
  echo "--- Building atm-sre/${name}:latest from ${context}/"
  docker build -t "atm-sre/${name}:latest" "${ROOT}/${context}"
done

echo ""
echo "==> All images built successfully."
echo ""
echo "To deploy the Swarm stack:"
echo "  1. Initialize swarm (if not already): docker swarm init"
echo "  2. Deploy:  docker stack deploy -c orchestration/swarm/docker-stack.yml atm"
echo "  3. Status:  docker stack services atm"
echo "  4. Remove:  docker stack rm atm"
