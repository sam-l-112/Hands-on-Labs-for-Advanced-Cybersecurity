# CERT C Secure Coding — 安全程式設計快速對照表

> 課堂版（Week 13 發下去用）。完整版見 [SEI CERT C Coding Standard](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/)

---

## 使用方法

1. 看 opencode 的輸出，**先憑感覺找「怪怪的地方」**
2. 翻這張表，給那個感覺取一個名字（CERT 規則 + CWE 編號）
3. 推論：「如果這個 smell 沒修，最壞會變成什麼 CVE？」
4. 寫進報告

---

## 記憶體與字串（最常被 opencode 寫錯）

| CERT 規則 | 一句話說明 | opencode 常見錯誤 | CWE | 真實案例 |
|-----------|-----------|-------------------|-----|---------|
| **STR31-C** | 字串儲存空間必須包含 `\0` 終止符（宣告 `buf[N]`，最多放 N-1 個字元） | `char buf[20]; gets(buf);` — 沒有長度限制 | [CWE-120](https://cwe.mitre.org/data/definitions/120.html) | Morris Worm (1988)、無數 buffer overflow |
| **STR07-C** | 使用 TR 24731 「安全版本」函式（`fgets`、`strncpy_s`、`snprintf`） | 用 `gets()`、`scanf("%s")`、`strcpy()` | [CWE-676](https://cwe.mitre.org/data/definitions/676.html) | Heartbleed 前身 |
| **STR02-C** | 傳入複雜子系統前先 sanitize | 直接把使用者輸入串進 SQL query 或 shell 指令 | [CWE-88](https://cwe.mitre.org/data/definitions/88.html) | SQL Injection（OWASP A03） |
| **MEM30-C** | 不要存取 `free()` 之後的記憶體 | 迴圈裡 `free(node)` 後仍讀 `node->next` | [CWE-416](https://cwe.mitre.org/data/definitions/416.html) | Chrome V8 多個 Use-After-Free CVE |
| **MEM31-C** | 每塊記憶體只 `free()` 一次 | 錯誤路徑多次釋放同一指標 | [CWE-415](https://cwe.mitre.org/data/definitions/415.html) | OpenSSL double-free |
| **EXP34-C** | `free()` 後把指標設為 `NULL`，解引用前先檢查 | `ptr = malloc(...); *ptr = x;`（未確認 malloc 成功）| [CWE-476](https://cwe.mitre.org/data/definitions/476.html) | NULL dereference crash |

---

## 整數運算

| CERT 規則 | 一句話說明 | opencode 常見錯誤 | CWE | 真實案例 |
|-----------|-----------|-------------------|-----|---------|
| **INT30-C** | 無號整數減法可能回繞（`0 - 1 = 4294967295`） | `size_t len = input_len - HEADER_SIZE;`（未確認大小順序）| [CWE-191](https://cwe.mitre.org/data/definitions/191.html) | libpng integer underflow |
| **INT32-C** | 有號整數溢位是 undefined behavior | `int n = INT_MAX; n++;` — 編譯器可能最佳化掉溢位檢查 | [CWE-190](https://cwe.mitre.org/data/definitions/190.html) | 各種 `malloc(n * sizeof(T))` overflow |

---

## 並行與競爭條件

| CERT 規則 | 一句話說明 | opencode 常見錯誤 | CWE | 真實案例 |
|-----------|-----------|-------------------|-----|---------|
| **CON30-C** | 共享資源存取前後加鎖 | 讀寫共享全域變數未用 mutex | [CWE-362](https://cwe.mitre.org/data/definitions/362.html) | Dirty Frag CVE-2026-43284 |
| **FIO45-C** | 避免 TOCTOU（check 和 use 之間狀態被改變） | `if (access(path, R_OK) == 0) { open(path); }` | [CWE-367](https://cwe.mitre.org/data/definitions/367.html) | Pack2TheRoot CVE-2026-41651（Week 12） |

---

## 秘密與憑證

| CERT 規則 | 一句話說明 | opencode 常見錯誤 | CWE | 真實案例 |
|-----------|-----------|-------------------|-----|---------|
| **MSC41-C** | 不要把密碼、金鑰、salt 寫死在程式碼裡 | `const char *SECRET_KEY = "abc123";` | [CWE-798](https://cwe.mitre.org/data/definitions/798.html) | Mirai botnet 預設密碼、Grafana TanStack（2026/05）|
| **MSC32-C** | 亂數種子必須不可預測（不用 `srand(time(0))`） | session token 用 `rand()` 生成 | [CWE-336](https://cwe.mitre.org/data/definitions/336.html) | PHP `mt_rand()` session 預測攻擊 |

---

## 錯誤處理

| CERT 規則 | 一句話說明 | opencode 常見錯誤 | CWE | 真實案例 |
|-----------|-----------|-------------------|-----|---------|
| **ERR33-C** | 每個函式呼叫都要確認回傳值 | `malloc(size);`（回傳值不存，不判 NULL）| [CWE-391](https://cwe.mitre.org/data/definitions/391.html) | 各種 crash-on-alloc-fail |
| **ERR07-C** | 錯誤訊息不洩漏內部路徑、stack trace、版本 | `printf("Error: %s not found at %s", input, internal_path);` | [CWE-209](https://cwe.mitre.org/data/definitions/209.html) | Heartbleed（回傳比預期更多的記憶體內容）|

---

## 本週 Lab 對照

| Lab | 主要訓練規則 |
|-----|------------|
| Lab 1（opencode 寫 VerifyPassword）| STR31-C、STR07-C、MSC41-C、ERR07-C |
| Lab 2（分析未知 CVE 片段）| CON30-C、FIO45-C（與 Week 12 TOCTOU 連結）|
| Lab 3（好指引下重寫）| 以上所有規則變成「好指引」的檢查清單 |

---

## CWE Top 20 快速參考（繁體中文）

> 資料來源：[GSS 資安電子報 0171 期](https://www.gss.com.tw/security-epaper/2272-gss-0171-CWE-checkmarx)，原始排名為 CWE Top 25（2019）。  
> CWE（Common Weakness Enumeration）由美國 CISA 贊助、MITRE 負責管理，提供軟體安全評估的共通語言。

| 排名 | CWE 編號 | 中文名稱 | 常見攻擊情境 |
|------|---------|---------|------------|
| 1 | [CWE-119](https://cwe.mitre.org/data/definitions/119.html) | 記憶體緩衝區操作不當 | Buffer overflow、stack smashing（林老師範例核心）|
| 2 | [CWE-79](https://cwe.mitre.org/data/definitions/79.html) | 跨網站腳本（XSS）| 注入惡意 script 至網頁 |
| 3 | [CWE-20](https://cwe.mitre.org/data/definitions/20.html) | 輸入驗證不當 | 未過濾的使用者輸入造成各類 injection |
| 4 | [CWE-200](https://cwe.mitre.org/data/definitions/200.html) | 資訊洩漏 | 錯誤訊息洩漏內部路徑、版本、stack trace |
| 5 | [CWE-125](https://cwe.mitre.org/data/definitions/125.html) | 越界讀取（OOB Read）| Heartbleed 即此類 |
| 6 | [CWE-89](https://cwe.mitre.org/data/definitions/89.html) | SQL 注入 | 直接將輸入拼入 SQL query |
| 7 | [CWE-416](https://cwe.mitre.org/data/definitions/416.html) | 釋放後使用（Use-After-Free）| `free(p)` 後繼續存取 `p` |
| 8 | [CWE-190](https://cwe.mitre.org/data/definitions/190.html) | 整數溢出或循環 | `malloc(n * size)` 的 n 溢位變成小值 |
| 9 | [CWE-352](https://cwe.mitre.org/data/definitions/352.html) | 跨站請求偽造（CSRF）| 誘使已登入用戶觸發惡意請求 |
| 10 | [CWE-22](https://cwe.mitre.org/data/definitions/22.html) | 路徑遍歷 | `../../etc/passwd` 讀取系統檔案 |
| 11 | [CWE-78](https://cwe.mitre.org/data/definitions/78.html) | OS 指令注入 | `system(user_input)` 執行任意指令 |
| 12 | [CWE-787](https://cwe.mitre.org/data/definitions/787.html) | 越界寫入（OOB Write）| 寫入超出陣列邊界，覆蓋相鄰記憶體 |
| 13 | [CWE-287](https://cwe.mitre.org/data/definitions/287.html) | 身分驗證不當 | 繞過登入驗證邏輯 |
| 14 | [CWE-476](https://cwe.mitre.org/data/definitions/476.html) | 空指標反參照 | `malloc()` 回傳 NULL 未判斷就使用 |
| 15 | [CWE-732](https://cwe.mitre.org/data/definitions/732.html) | 關鍵資源權限分配不當 | 設定檔、私鑰權限過於寬鬆 |
| 16 | [CWE-434](https://cwe.mitre.org/data/definitions/434.html) | 危險類型檔案上傳無限制 | 上傳 `.php` webshell |
| 17 | [CWE-611](https://cwe.mitre.org/data/definitions/611.html) | XML 外部實體參考限制不當（XXE）| 讀取伺服器本地檔案 |
| 18 | [CWE-94](https://cwe.mitre.org/data/definitions/94.html) | 程式碼生成控制不當 | `eval(user_input)`、動態程式碼執行 |
| 19 | [CWE-798](https://cwe.mitre.org/data/definitions/798.html) | 硬編碼認證資訊 | 密碼、API key 寫死在原始碼 |
| 20 | [CWE-400](https://cwe.mitre.org/data/definitions/400.html) | 資源消耗無控制 | 無限迴圈、大量分配記憶體導致 DoS |

> **偵測工具建議**：可使用 SAST 工具（如 [Checkmarx](https://checkmarx.com/)、[Semgrep](https://github.com/semgrep/skills)）自動掃描上表弱點。

---

> **參考資料**
> - [CMU SEI CERT C Coding Standard](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/)
> - [CWE Top 25 Most Dangerous Software Weaknesses](https://cwe.mitre.org/top25/)
> - [GSS 資安電子報 0171 期 — CWE Top 25 說明](https://www.gss.com.tw/security-epaper/2272-gss-0171-CWE-checkmarx)
> - [OWASP Top 10 (2021)](https://owasp.org/Top10/)
