#!/usr/bin/env bash
set -e

echo "=== Telegram PC Control - Server Setup ==="

# 1. Проверка и установка Python/venv/pip
echo "[1/4] Installing system dependencies (python3, venv, pip)..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# 2. Переход в директорию скрипта (корень проекта)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 3. Создание и активация виртуального окружения
if [ ! -d "venv" ]; then
  echo "[2/4] Creating Python virtual environment..."
  python3 -m venv venv
fi

echo "[2/4] Activating virtual environment..."
# shellcheck disable=SC1091
source venv/bin/activate

# 4. Установка Python-зависимостей для бота
echo "[3/4] Upgrading pip and installing Python packages..."
pip install --upgrade pip
pip install pytelegrambotapi flask waitress requests pillow

# 5. Сбор данных для .env
echo "[4/4] Creating .env for bot..."

read -rp "Enter TELEGRAM BOT TOKEN: " BOT_TOKEN
while [ -z "$BOT_TOKEN" ]; do
  echo "Token cannot be empty."
  read -rp "Enter TELEGRAM BOT TOKEN: " BOT_TOKEN
done

read -rp "Enter AUTHORIZED PASSWORD (for Telegram access): " AUTH_PASSWORD
while [ -z "$AUTH_PASSWORD" ]; do
  echo "Password cannot be empty."
  read -rp "Enter AUTHORIZED PASSWORD (for Telegram access): " AUTH_PASSWORD
done

IP_DEFAULT="164.215.97.151"
read -rp "Enter public IP for ADVERTISED_IP [${IP_DEFAULT}]: " ADV_IP
ADV_IP=${ADV_IP:-$IP_DEFAULT}

PORT_DEFAULT="25565"
read -rp "Enter bot port [${PORT_DEFAULT}]: " BOT_PORT
BOT_PORT=${BOT_PORT:-$PORT_DEFAULT}

# 6. Создание .env в каталоге bot/
BOT_DIR="${SCRIPT_DIR}/bot"
mkdir -p "$BOT_DIR"

cat > "${BOT_DIR}/.env" <<EOF
ADVERTISED_IP=${ADV_IP}
BOT_PORT=${BOT_PORT}
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
AUTHORIZED_PASSWORD=${AUTH_PASSWORD}
EOF

echo
echo "✅ Setup finished."
echo "📂 Project directory: ${SCRIPT_DIR}"
echo "📁 Bot directory: ${BOT_DIR}"
echo "📄 .env created in bot/:"
cat "${BOT_DIR}/.env" || true
echo
echo "Для запуска бота:"
echo "  cd \"${SCRIPT_DIR}\""
echo "  source venv/bin/activate"
echo "  python3 bot/bot.py"
echo
echo "Не забудь открыть порт ${BOT_PORT}/tcp в ufw или firewall."