# Week 10 — Operation 竹流入侵

**日期**：2026/05/04–05/10
**時長**：1 小時

---

## 角色分工

| 角色 | 任務 |
|------|------|
| Blue Team | 執行 `server.py` 建起靶機，將 IP 告知紅隊，**攻擊期間不得修改程式碼** |
| Red Team | 透過 4 種不同漏洞找出 4 個 Flag |

---

## 環境準備

```bash
pip install flask requests
```

驗證：
```bash
python3 -c "import flask, requests; print('OK')"
```

---

## 課堂流程（60 分鐘）

| 時間 | 活動 |
|------|------|
| 0:00–0:05 | 老師說明新竹物流事件背景與 4 個 CVE |
| 0:05–0:10 | 藍隊啟動靶機，紅隊讀關卡說明 |
| 0:10–0:45 | **CTF 攻擊時間**（35 分鐘，4 個關卡） |
| 0:45–0:55 | **藍隊現場修補**，紅隊嘗試繞過 |
| 0:55–1:00 | 計分 + 複盤 |

---

## Blue Team：啟動靶機

```bash
python3 server.py
```

靶機啟動後顯示：
```
[*] 竹流靶機已啟動：http://0.0.0.0:5000
[*] Flag 1 已寫入 /tmp/flag1.txt
[*] Flag 2 已寫入 /tmp/logistics_db.txt
[*] Flag 3 已藏入 app.config（需 SSTI 才能讀）
[*] Flag 4 在 /admin（需 SSRF 才能存取）
```

將靶機 IP 告知紅隊。

---

## Red Team：4 個關卡

| # | CVE | 漏洞類型 | 難度 | 攻擊入口 |
|---|-----|----------|------|----------|
| 🟢 Flag 1 | CVE-2026-39808 | Command Injection | Easy | `/track?id=` |
| 🟡 Flag 2 | CVE-2021-41773 | Path Traversal | Medium | `/download?file=` |
| 🟠 Flag 3 | CVE-2022-22963 | SSTI | Hard | `/greet?name=` |
| 🔴 Flag 4 | CVE-2021-26855 | SSRF | Hard | `/fetch?url=` |

---

### 🟢 Flag 1 — Command Injection（ CVE-2026-39808）

**漏洞描述**：伺服器將使用者輸入的單號直接拼接進 shell 指令執行

**入口**：`http://<IP>:5000/track?id=<payload>`

**攻擊方式**：用 `;` 或 `&&` 接在單號後面追加指令

**Payload**：
```
http://<IP>:5000/track?id=;cat /tmp/flag1.txt
```

**提示**：用 `;` 或 `&&` 接在單號後面追加指令，確認能執行後再讀 `/tmp/flag1.txt`

**Flag**：`FLAG{cmd_injection_cve_2026_39808}`

---

### 🟡 Flag 2 — Path Traversal（CVE-2021-41773）

**漏洞描述**：伺服器用 `/download?file=` 提供公告檔案下載，但未限制路徑範圍

**入口**：`http://<IP>:5000/download?file=<payload>`

**攻擊方式**：用 `../` 往上跳出公告目錄

**Payload**：
```
http://<IP>:5000/download?file=../../tmp/logistics_db.txt
```

**提示**：嘗試用 `../` 往上跳出公告目錄，目標是 `/tmp/logistics_db.txt`。需要幾層 `../` 才能從 `/tmp/www_public/` 跳到 `/tmp/`？

**Flag**：`FLAG{path_traversal_cve_2021_41773}`

---

### 🟠 Flag 3 — SSTI（ CVE-2022-22963）

**漏洞描述**：伺服器將使用者輸入的名字直接放進 Jinja2 模板渲染，輸入的 `{{ }}` 會被執行

**入口**：`http://<IP>:5000/greet?name=<payload>`

**攻擊方式**：先用 `{{7*7}}` 確認模板有被執行，再讀取 config

**Payload**：
```
http://<IP>:5000/greet?name={{config}}
```

**提示**：先用 `{{7*7}}` 確認模板有被執行（回應會出現 49）。Flag 藏在 Flask 的 config 物件裡

**Flag**：`FLAG{ssti_cve_2022_22963}`

---

### 🔴 Flag 4 — SSRF（ CVE-2021-26855）

**漏洞描述**：伺服器提供 `/fetch?url=` 讓外部物流系統回傳狀態，但未過濾內網位址。Flag 藏在只允許本機存取的 `/admin` 頁面

**入口**：`http://<IP>:5000/fetch?url=<payload>`

**攻擊方式**：讓靶機自己去打自己的 `/admin`

**Payload**：
```
http://<IP>:5000/fetch?url=http://127.0.0.1:5000/admin
```

**提示**：讓靶機自己去打自己的 `/admin`，從靶機出去的請求 `remote_addr` 是什麼？

**Flag**：`FLAG{ssrf_cve_2021_26855}`

---

## 第二回合：藍隊現場修補（10 分鐘）

攻擊時間結束，藍隊依序將 4 個漏洞函式替換為安全版本

### Flag 1 修補（Allowlist）
```python
import re

@app.route("/track")
def track():
    order_id = request.args.get("id", "")
    if not re.fullmatch(r"\d{1,10}", order_id):
        return "無效單號格式", 400
    result = subprocess.run(
        f"echo 查詢單號: {order_id}", shell=True, capture_output=True, text=True
    )
    return f"<pre>{result.stdout}</pre>"
```

### Flag 2 修補（路徑正規化）
```python
import os

@app.route("/download")
def download():
    filename = request.args.get("file", "notice.txt")
    safe_path = os.path.realpath(f"{PUBLIC_DIR}/{filename}")
    if not safe_path.startswith(PUBLIC_DIR):
        return "禁止存取", 403
    with open(safe_path, "r") as f:
        return f"<pre>{f.read()}</pre>"
```

### Flag 3 修補（禁用動態模板）
```python
from flask import escape

@app.route("/greet")
def greet():
    name = escape(request.args.get("name", "訪客"))
    return f"<h2>您好，{name}！您的貨件正在處理中。</h2>"
```

### Flag 4 修補（封鎖內網位址）
```python
import ipaddress

@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    from urllib.parse import urlparse
    host = urlparse(url).hostname
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback:
            return "禁止存取內網位址", 403
    except Exception:
        pass
    resp = requests.get(url, timeout=3)
    return f"<pre>{resp.text}</pre>"
```

---

## 繳交說明

本週實作結果請依 `pentest-report-template.md` 格式繳交滲透測試報告，每人一份。

**檔名格式**：`W10_滲透測試報告_學號_姓名.docx`
**截止日期**：上課當週週日 23:59