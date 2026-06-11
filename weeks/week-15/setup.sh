#!/bin/bash
# Week 15 Lab 環境建置
# 使用方式：sudo bash setup.sh

set -e

STUDENT_USER="${SUDO_USER:-$USER}"
LAB_DIR="/home/${STUDENT_USER}/pentest/week15"

echo "[*] Week 15 Lab 環境設定"
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

# --- 2. DVWA ---
echo "[*] 拉取 DVWA image（首次約 1-2 分鐘）..."
docker pull kaakaww/dvwa-docker:latest

docker rm -f dvwa 2>/dev/null && echo "[*] 移除舊 container" || true

echo "[*] 啟動 DVWA on port 80..."
docker run -d \
  --name dvwa \
  -p 80:80 \
  -p 3306:3306 \
  kaakaww/dvwa-docker:latest

echo "[*] 等待服務啟動（15 秒）..."
sleep 15

# 確認服務存活
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/login.php || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  echo "[+] DVWA 啟動成功：http://localhost/login.php"
else
  echo "[!] 服務可能尚未就緒（HTTP $HTTP_CODE），稍後請手動確認"
fi

# --- 3. Lab 資料夾結構 ---
echo "[*] 建立 Lab 資料夾..."
mkdir -p "$LAB_DIR"/{evidence,logs,reports}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/pentest-report-template.md" "$LAB_DIR/reports/"
chown -R "${STUDENT_USER}:${STUDENT_USER}" "$LAB_DIR"

# --- 4. 安裝 gobuster（偵察工具）---
if ! command -v gobuster &>/dev/null; then
  echo "[*] 安裝 gobuster..."
  apt install -y gobuster 2>/dev/null || echo "[!] gobuster 安裝失敗，請手動安裝"
fi

echo ""
echo "================================================"
echo "[+] 設定完成"
echo ""
echo "  DVWA          : http://localhost/login.php"
echo "  帳號 / 密碼   : admin / password"
echo "  Lab 資料夾    : $LAB_DIR"
echo ""
echo "[!] 進入 DVWA 後，先到 DVWA Security 把難度設為 Low"
echo "[!] 再到 Setup / Reset DB 初始化資料庫"
echo "================================================"
