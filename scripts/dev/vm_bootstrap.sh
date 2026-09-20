#!/usr/bin/env bash
# One-time bootstrap for a fresh Ubuntu 24.04 VM (Azure B2s, Oracle A1, DO droplet).
# Usage:  curl -fsSL <raw-url> | bash   OR   bash vm_bootstrap.sh
# After data upload completes it serves:  http://<VM_IP>:8080
set -euo pipefail
[ "${EUID:-$(id -u)}" -eq 0 ] || { echo "Run as root (sudo bash $0)"; exit 1; }

APP_DIR="${APP_DIR:-/opt/app}"
BRANCH="${BRANCH:-v2-recovery-parity}"

echo "== 1/5 Docker =="
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh

echo "== 2/5 Swap (2G — the flood sim wants headroom) =="
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "== 3/5 Firewall (8080 frontend, 22 ssh) =="
if command -v ufw >/dev/null; then ufw allow 22/tcp >/dev/null 2>&1 || true; ufw allow 8080/tcp >/dev/null 2>&1 || true; fi

echo "== 4/5 Repository =="
if [ ! -d "$APP_DIR/.git" ]; then
  git clone -b "$BRANCH" https://github.com/lakshyashahi0712/sih2026-urban-flood-nowcasting.git "$APP_DIR"
fi

echo "== 5/5 Data check + launch =="
if [ -z "$(ls -A "$APP_DIR/data" 2>/dev/null)" ]; then
  echo
  echo "  !! data/ is EMPTY — the Delhi API will report NOT_READY until you upload it."
  echo "  !! From YOUR PC (Git Bash), run:"
  echo "      scp -r data/* root@<VM_IP>:$APP_DIR/data/"
  echo "  !! then: ssh root@<VM_IP> 'cd $APP_DIR && docker compose up -d --build'"
  echo
fi
cd "$APP_DIR"
docker compose up -d --build
sleep 3
curl -fsS http://localhost:8080/health && echo "  <- frontend+API OK on :8080"
