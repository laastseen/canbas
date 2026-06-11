#!/bin/bash
set -euo pipefail

APP_DIR="/var/www/canbas"
VENV="$APP_DIR/venv"
ENV_FILE="$APP_DIR/private/.env"
SEED="${1:-}"

echo "==> App dir: $APP_DIR"
cd "$APP_DIR"

git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true

echo "==> Before update:"
git log -1 --oneline

echo "==> Pull latest code"
git fetch origin master
git reset --hard origin/master

echo "==> After update:"
git log -1 --oneline

echo "==> Install dependencies"
source "$VENV/bin/activate"
pip install -r requirements.txt -q

echo "==> Load environment"
set -a
source "$ENV_FILE"
set +a

echo "==> Database migration"
flask db upgrade || true

if [ "$SEED" = "--seed" ]; then
  echo "==> Seed demo data (force)"
  python seed.py --force
fi

echo "==> Fix permissions"
chown -R canbas:canbas "$APP_DIR"

echo "==> Restart service"
systemctl restart canbas
sleep 2
systemctl is-active canbas

echo "==> Verify endpoints"
for path in / /privacy /cookies /auth/register; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000${path}")
  echo "  ${path} -> ${code}"
done

echo "==> Done"
echo "Site: http://178.253.38.79"
echo "Privacy: http://178.253.38.79/privacy"
