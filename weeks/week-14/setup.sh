#!/bin/bash
# Week 14 Lab 環境建置
# 使用方式：sudo bash setup.sh

set -e

STUDENT_USER="${SUDO_USER:-$USER}"
LAB_DIR="/home/${STUDENT_USER}/pentest/week14"

echo "[*] Week 14 Lab 環境設定"
echo "================================"

# --- 1. Docker 檢查與安裝 ---
if ! command -v docker &>/dev/null; then
  echo "[*] 安裝 Docker..."
  apt update -qq && apt install -y docker.io
  systemctl enable docker
  systemctl start docker
  usermod -aG docker "$STUDENT_USER"
  echo ""
  echo "[!] Docker 剛安裝完成。請重新登入（或執行 newgrp docker），再重跑 setup.sh"
  exit 0
fi

if ! systemctl is-active --quiet docker; then
  echo "[*] 啟動 Docker..."
  systemctl start docker
fi

# --- 2. Juice Shop ---
echo "[*] 拉取 Juice Shop image（首次約 2-3 分鐘）..."
docker pull bkimminich/juice-shop:latest

docker rm -f juice-shop 2>/dev/null && echo "[*] 移除舊 container" || true

echo "[*] 啟動 Juice Shop on port 3000..."
docker run -d \
  --name juice-shop \
  -p 3000:3000 \
  bkimminich/juice-shop:latest

echo "[*] 等待服務啟動（20 秒）..."
sleep 20

# 確認服務存活
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
  echo "[+] Juice Shop 啟動成功：http://localhost:3000"
else
  echo "[!] 服務可能尚未就緒，請稍等後手動確認：curl http://localhost:3000"
fi

# --- 3. Lab 資料夾結構 ---
echo "[*] 建立 Lab 資料夾..."
mkdir -p "$LAB_DIR"/{evidence,logs,reports}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/wordlist-top50.txt" "$LAB_DIR/"
cp "$SCRIPT_DIR/finding-template.md" "$LAB_DIR/reports/"
chown -R "${STUDENT_USER}:${STUDENT_USER}" "$LAB_DIR"

echo ""
echo "================================================"
echo "[+] 設定完成"
echo ""
echo "  Juice Shop  : http://localhost:3000"
echo "  Lab 資料夾  : $LAB_DIR"
echo "  Wordlist    : $LAB_DIR/wordlist-top50.txt"
echo ""
echo "[!] 提醒：所有 Lab 指令請在 $LAB_DIR 底下執行"
echo "================================================"
