#!/bin/bash
set -e

APP_DIR="/var/www/canbas"
VENV="$APP_DIR/venv"
ENV_FILE="$APP_DIR/private/.env"

echo "==> Pull latest code"
cd "$APP_DIR"
git pull origin master

echo "==> Install dependencies"
source "$VENV/bin/activate"
pip install -r requirements.txt

echo "==> Load environment"
set -a
source "$ENV_FILE"
set +a

echo "==> Database migration"
flask db upgrade || true

echo "==> Seed demo data (force)"
python seed.py --force

echo "==> Fix permissions"
chown -R canbas:canbas "$APP_DIR"

echo "==> Restart service"
systemctl restart canbas
systemctl status canbas --no-pager

echo "==> Done"
echo "Site:  http://vm4361050.firstbyte.club"
echo "Admin: admin@canbas.ru / admin123"
