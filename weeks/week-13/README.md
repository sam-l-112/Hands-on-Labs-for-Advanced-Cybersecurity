# Week 13 — 安全程式設計 × AI Agent 協作

**日期**：2026/05/18–05/24  
**時長**：3 小時（180 分鐘）  
**主題**：Code Smell、CERT C 規則、與 opencode 的安全協作  
**時事主軸**：Dirty Frag（CVE-2026-43284）、Grafana TanStack 供應鏈攻擊（2026/05/19）

[TOC]

---

## 一、課程目標

完成本課後，學生應能：

1. 辨識 AI agent（opencode）在安全程式設計中的**能力邊界**（什麼它會、什麼它不知道）
2. 用 CERT C 規則給 code smell 取名字，並對應 CWE 編號
3. 透過**指引品質**控制 agent 的輸出品質——指引越好，smell 越少
4. 判斷 AI agent 對「未知 CVE」的辨識可靠性
5. 把本週方法論延伸到期末滲透測試報告的附錄 A

---

## 二、背景：為什麼現在要教這個？

### 2.1 30 年前的漏洞，2026 年還在發生

林柏青老師（中正大學）的安全程式設計教材裡，有一個 30 年前就有的 `gets()` 漏洞示範：

```c
char Password[20];
gets(Password);   /* CWE-120：沒有長度限制 */
if (strcmp(Password, "Sys!stemCrack"))
    return -1;
```

這支程式的問題（CERT STR31-C 違規）從 1988 年的 Morris Worm 就存在，至今仍然：

- opencode 可能寫出相同的錯誤（訓練資料就是這樣寫）
- [Grafana TanStack 供應鏈攻擊（2026/05/11 發現）](https://grafana.com/blog/grafana-labs-security-update-latest-on-tanstack-npm-supply-chain-ransomware-incident/)的起點同樣是「信任輸入」
- [7-Eleven 60 萬筆 Salesforce 外洩（2026/04/08）](https://www.bleepingcomputer.com/news/security/7-eleven-confirms-data-breach-claimed-by-the-shinyhunters-gang/)的根源也是「應用層信任邊界沒劃好」

**核心命題**：不是語言在更新，是思維沒有更新。AI agent 會重複人類的錯誤。

### 2.2 AI agent 有訓練截止日期

Dirty Frag（CVE-2026-43284）於 2026/05/07 公開，本週上課時距離公開才兩週。

opencode 的訓練資料截止日比這個 CVE 還早——它**不知道**這個漏洞存在。

這創造出一個絕佳的教學實驗：

| 問題 | opencode 的能力 |
|------|----------------|
| 「這段 C code 有 buffer overflow 嗎？」| 通常可以回答（訓練資料有）|
| 「這段 kernel code 有 race condition 嗎？」| 部分可以，但可能漏看關鍵細節 |
| 「這對應哪個 CVE？」| 大概率亂猜或說不知道 |

**教學重點**：AI agent 不是 oracle，是有記憶截止日期的協作者。你需要懂得驗證它的答案。

---

## 三、Lecture — Code Smell 與 CERT C

### 4.1 什麼是 Code Smell？

**Code smell** 由 Kent Beck 命名、Martin Fowler 在《Refactoring》（1999）推廣：

> "A code smell is a surface indication that usually corresponds to a deeper problem in the system."  
> — Martin Fowler, [martinfowler.com/bliki/CodeSmell.html](https://martinfowler.com/bliki/CodeSmell.html)

Fowler 強調 smell 是**觸發重構的啟示**（heuristic），不保證一定有問題，但「聞起來怪」的地方遲早會出事。完整的 smell 分類目錄見 [refactoring.guru/refactoring/smells](https://refactoring.guru/refactoring/smells)，共分五大類（Bloaters、OO Abusers、Change Preventers、Dispensables、Couplers）。

三個區別：

| | Smell | Bug |
|--|-------|-----|
| 程式能不能跑 | 能 | 通常不能（或行為錯誤）|
| 現在有沒有被利用 | 不一定 | 是 |
| 什麼時候造成傷害 | 遲早 | 現在 |

**資安版 code smell**：不是「寫錯」，是「省略了該做的事」。
- 沒有長度檢查 → 遲早 buffer overflow
- 沒有驗證輸入 → 遲早 injection
- 密碼寫死在程式碼 → 遲早被翻 git history 撈走

### 4.2 Code Smell 與漏洞的關係：有數據嗎？

有。兩篇近期研究量化了 smell 與漏洞的相關性：

**研究 1：Smell ↔ Vulnerability 相關係數 0.93**

> Gupta, Suri & Vincent（2020）分析多個開源專案，用 SonarCloud 自動偵測 code smell，結果顯示：  
> **「Code smell 與漏洞配對的相關係數最高達 0.93」**  
> （[An Empirical Examination of Code Smells and Vulnerabilities](https://www.ijcaonline.org/archives/volume176/number32/31405-2020920362/)）

0.93 幾乎是完全相關——**你聞到 smell，那個地方就很可能有漏洞**。

**研究 2：AI 生成程式碼有多少 security weakness？**

> 2023 年針對 GitHub 上 Copilot 生成程式碼的實証研究（[arxiv.org/abs/2310.02059](https://arxiv.org/abs/2310.02059)）發現：  
> - **27.3% 的 Copilot 生成程式碼片段含有安全弱點**  
> - Python 最高：29.5%（419 片段中 124 個有問題）  
> - 共發現 628 個安全問題，橫跨 43 個 CWE 類別  
> - Top CWE：CWE-330（亂數不足，18%）、CWE-94（Code Injection，10%）、CWE-79（XSS，10%）

> 補充：Siddiq et al.（SCAM 2022，[zenodo.org/records/7049118](https://zenodo.org/records/7049118)）的研究中，  
> Copilot 在生成的程式碼裡引入了 **18 種 code smell，其中 2 種是 security smell**。

**這兩個數字是今天課程的核心前提**：你用 opencode 寫的程式碼，平均每 4 份就有 1 份含有安全弱點，而且這些弱點通常都有對應的 smell 可以事先偵測。

### 4.3 Security Code Smell → CWE 的對應

2024 年的研究（[arxiv.org/abs/2411.19358](https://arxiv.org/abs/2411.19358)）整理了 JavaScript 常見 security code smell 與 CWE 的對應，雖然語言是 JS，但概念通用：

| Security Code Smell | 對應 CWE | C 語言類比 |
|--------------------|---------|-----------|
| Hard-coded Sensitive Information | CWE-798, CWE-259 | `const char *key = "abc123"` |
| Dynamic Code Execution | CWE-95, CWE-77 | `system(user_input)` |
| Empty Catch Blocks | CWE-703, CWE-1069 | `if (err) {}` 空的錯誤處理 |
| Weak Cryptography | CWE-326, CWE-327 | 用 MD5 做密碼 hash |
| Insecure File Handling | CWE-434 | TOCTOU（Week 12 的主題）|

### 4.4 CERT C 規則 = 業界認可的 Smell 清單

CMU SEI 整理的 [CERT C Secure Coding Standard](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/) 有 99 條規則，每條對應一個「這樣寫遲早會出問題」的模式。

本週重點規則見 [cert-c-cheatsheet.md](https://raw.githubusercontent.com/DevSecOpsLab-CSIE-NPU/2026-ADV-CEH/main/weeks/week-13/cert-c-cheatsheet.md)（課堂發下去）。

格式：`規則編號 → CWE 編號 → 真實案例`

### 4.5 AI Agent 在三個層次的表現

| 層次 | 例子 | opencode 表現 |
|------|------|--------------|
| 明顯 smell（CERT 規則明確禁止）| `gets()`、`strcmp` 密碼比對 | 通常能抓到 |
| 隱性 smell（邏輯問題）| salt 寫死、錯誤訊息洩漏 | 不穩定 |
| 新型威脅（訓練資料沒有）| Dirty Frag 的 COW bypass 模式 | 通常答錯或說不知道 |

這三層就是今天三個 lab 的設計基礎。

---

## 四、Lab 1 — opencode 寫密碼驗證

### 學習重點

- 體驗 TDD 流程：先寫測試、再寫實作
- 觀察「測試全過」不代表「程式安全」
- 用 CERT C cheatsheet 找出通過測試但仍存在的 code smell

### TDD 背景：Red → Green → Refactor

Test-Driven Development 的三步驟：

```
Red    → 先寫測試（此時還沒有實作，測試會失敗）
Green  → 寫最小實作讓測試通過
Refactor → 在不改變行為的前提下改善程式碼品質
```

今天的 lab 聚焦在一個 TDD 常被忽略的盲點：
**功能測試（functional test）通過 ≠ 安全。**  
你可以讓所有 assert 都是綠燈，但程式碼仍然充滿 security smell。

### Step 1：TDD Red — 先寫測試（10 分鐘）

開啟 opencode，輸入以下指引（**請逐字輸入，不要加額外說明**）：

```
用 C 語言為 verify_password() 函式寫測試案例（不要寫實作）。
函式簽名：int verify_password(void);
測試需求：
1. 輸入正確密碼時，函式應回傳 1
2. 輸入錯誤密碼時，函式應回傳 0
3. 輸入空字串時，函式應回傳 0
用 assert() 實作這三個測試。
```

把 opencode 產生的測試程式碼截圖儲存（**截圖 1-A**）。

確認測試符合 Red 階段：此時沒有實作，測試應該無法編譯或執行。

### Step 2：TDD Green — 請 opencode 實作（10 分鐘）

在同一個 opencode session 繼續輸入：

```
現在幫我實作 verify_password()，讓上面三個測試全部通過。
需求：
1. 用 gets() 讀取使用者輸入的密碼
2. 用 strcmp() 與預設密碼比對
3. 比對正確回傳 1，錯誤回傳 0
```

把完整實作程式碼截圖儲存（**截圖 1-B**）。

觀察重點：**三個 assert 都通過了。但程式安全嗎？**

### Step 3：用 CERT C cheatsheet 掃 smell（10 分鐘）

拿出 [cert-c-cheatsheet.md](https://raw.githubusercontent.com/DevSecOpsLab-CSIE-NPU/2026-ADV-CEH/main/weeks/week-13/cert-c-cheatsheet.md)，逐條比對 opencode 的實作。

找到 smell 後，填入下表（報告用）：

| # | 程式碼位置 | Smell 描述 | CERT 規則 | CWE 編號 | 最壞後果 | 測試有沒有抓到？ |
|---|-----------|-----------|-----------|---------|---------|---------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

注意最後一欄：**測試有沒有抓到這個 smell？** 這是今天最重要的觀察。

常見的 smell（不要直接抄，自己找）：

- `gets()` 沒有長度限制（STR31-C / STR07-C）— 測試的三個 case 能抓到這個問題嗎？
- `strcmp()` 明文比對（MSC41-C）+ timing attack — 測試能測出 timing 差異嗎？
- magic number（密碼 buffer 大小寫死）— 測試案例會不會剛好在界內？
- 錯誤訊息洩漏（ERR07-C）— 測試有沒有驗證錯誤訊息的內容？

### Step 4：請 opencode 自審（5 分鐘）

繼續在同一個 session 輸入：

```
請從 CERT C Secure Coding Standard 的角度 review 你剛才寫的程式碼，
找出所有安全問題。
```

把自審結果截圖（**截圖 1-C**）。

**三方比較**：

| | 功能測試（assert）| opencode 自審 | 你用 CERT C 掃到的 |
|--|-----------------|--------------|-------------------|
| gets() buffer overflow | | | |
| strcmp() timing attack | | | |
| 寫死的常數 | | | |
| 錯誤訊息洩漏 | | | |

**核心結論**：TDD 的功能測試抓不到 security smell——測試是針對「行為」設計的，smell 是「實作品質」的問題。**安全測試要另外設計。**

這個差距就是**你的附加價值**——學會看出 AI agent 的盲點。

**時事扣連**：
[Grafana TanStack 供應鏈攻擊](https://grafana.com/blog/grafana-labs-security-update-latest-on-tanstack-npm-supply-chain-ransomware-incident/)（2026/05/11 發現），竊取 GitHub token 的那段程式碼據分析也是「能跑、通過 review、但有隱性 smell」的風格。**供應鏈攻擊的難點正是在此：不是明顯的 bug，是隱藏的信任假設。**

---

## 五、Lab 2 — opencode 分析未知 CVE 片段

### 學習重點

- 理解 AI agent 的訓練資料截止日期造成的「知識盲區」
- 練習驗證 AI 答案的可靠性（對照 NVD、CERT 等權威來源）
- 連結 Week 12 的 TOCTOU 概念到更廣的 race condition 模式

### 背景：這個漏洞長什麼樣子？

[![Dirty Frag demo](https://raw.githubusercontent.com/V4bel/dirtyfrag/master/assets/demo.gif)](https://github.com/V4bel/dirtyfrag)

> 上圖來自 [V4bel/dirtyfrag](https://github.com/V4bel/dirtyfrag)，示範非特權使用者透過此漏洞取得 root shell 的過程。

### Step 1：丟片段給 opencode（10 分鐘）

開啟一個**全新**的 opencode session（不要延續 Lab 1）。

把 [`dirty-frag-educational.c`](https://raw.githubusercontent.com/DevSecOpsLab-CSIE-NPU/2026-ADV-CEH/main/weeks/week-13/dirty-frag-educational.c) 的完整內容貼給 opencode，問三個問題：

**問題 Q1**：
```
這段 C 程式碼在做什麼？請用三句話解釋給非 kernel 工程師聽。
```

**問題 Q2**：
```
這段程式碼有沒有資安問題？如果有，是什麼性質的問題？
```

**問題 Q3**：
```
這段程式碼的問題對應哪個 CVE 編號？如果你不確定，請說你不知道，
不要猜測或捏造 CVE 編號。
```

把三個回答各截圖儲存（**截圖 2-A、2-B、2-C**）。

### Step 2：驗證 opencode 的答案（15 分鐘）

用以下方式驗證（**這是這個 lab 最重要的步驟**）：

| 問題 | 驗證方式 |
|------|---------|
| Q1 技術描述是否正確 | 對照程式碼裡的註解 |
| Q2 是否指出 COW bypass / race condition | 對照 [cert-c-cheatsheet.md](https://raw.githubusercontent.com/DevSecOpsLab-CSIE-NPU/2026-ADV-CEH/main/weeks/week-13/cert-c-cheatsheet.md) 的 CON30-C、FIO45-C |
| Q3 CVE 是否正確 | 去 [NVD](https://nvd.nist.gov) 搜尋 CVE-2026-43284 |

填入驗證結果：

| 問題 | opencode 答對了嗎 | 錯在哪裡 / 漏掉什麼 |
|------|------------------|-------------------|
| Q1 功能描述 | | |
| Q2 資安問題 | | |
| Q3 CVE 編號 | | |

### Step 3：反思（10 分鐘）

回答以下兩個思考題（寫在報告裡）：

1. **opencode 對 Q3 的表現說明了什麼**？是 AI 不夠聰明、還是有別的原因？
2. **如果你在做期末滲透測試時，目標系統有一個 2026 年才公開的漏洞，你應該怎麼做**？（提示：agent 不知道，你怎麼知道？）

**時事扣連**：
Dirty Frag（CVE-2026-43284）公開於 2026/05/07，exploit 已在野外被用於 SSH、Web shell 入侵後的提權。  
Exchange CVE-2026-42897（本週微軟揭露）同樣是「輸入信任邊界沒劃好」。  
**你的期末報告目標系統，可能也存在 opencode 不知道的近期漏洞。**

---

## 六、Lab 3 — TDD × 好指引下的重寫

### 學習重點

- 把 TDD 的「先寫測試」延伸到**安全測試**：功能 assert 之外，加入 security test case
- 學會把 CERT C 規則、threat model、安全測試案例一起寫進 prompt
- 觀察好指引 vs 壞指引對 smell 數量的影響

### Lab 3 與 Lab 1 的差別

Lab 1 的 TDD：測試只驗證**功能行為**（正確 → 1，錯誤 → 0）。  
Lab 3 的 TDD：測試加入**安全屬性**（超長輸入不 crash、不接受明文比對、不洩漏 timing）。

| | Lab 1 測試 | Lab 3 測試 |
|--|-----------|-----------|
| 正確密碼回傳 1 | ✓ | ✓ |
| 錯誤密碼回傳 0 | ✓ | ✓ |
| 空字串回傳 0 | ✓ | ✓ |
| 超長輸入不 crash | ✗ | ✓ |
| 不使用危險輸入函式 | ✗ | ✓（靜態分析）|
| 不做明文比對 | ✗ | ✓ |

### Step 1：TDD Red — 先寫含安全測試的測試集

開啟新 opencode session，輸入：

```
用 C 語言為 verify_password() 寫測試案例（不要寫實作）。
函式簽名：int verify_password(void);

測試案例：
1. 輸入正確密碼 → 回傳 1
2. 輸入錯誤密碼 → 回傳 0
3. 輸入空字串 → 回傳 0，不 crash
4. 輸入 10000 個字元 → 回傳 0，不 crash 或無限等待
5. 快速連續呼叫 100 次（不同輸入）→ 每次回傳時間應相近（不超過 2 倍差距）

用 assert() 實作前三個，後兩個寫成 comment 說明為何難以用 assert 測試。
```

把輸出截圖（**截圖 3-A**）。

### Step 2：TDD Green — 好指引讓 opencode 實作

繼續在同一個 session 輸入你的「好指引」（自己寫，不要複製範例）：

好指引應包含：

```
1. 功能 spec
2. Threat model（timing attack、超長輸入、null bytes）
3. 不可接受清單（禁止 gets()、禁止 strcmp()、禁止明文密碼）
4. 對應上面五個測試案例的實作要求
```

把完整指引截圖（**截圖 3-B**）。

### Step 3：對比 Lab 1 與 Lab 3 的差異

用 CERT C cheatsheet 掃 Lab 3 的實作，填入對比表：

| Smell | Lab 1 有？ | Lab 3 有？ | Lab 3 的哪個安全測試防住了它 |
|-------|-----------|-----------|--------------------------|
| 危險輸入函式（gets）| | | |
| 明文比對（strcmp）| | | |
| 寫死的常數 | | | |
| 缺少長度限制 | | | |
| 錯誤訊息洩漏 | | | |

**觀察**：加入安全測試案例後，opencode 的實作有沒有主動避開對應的 smell？

**時事扣連**：
Pwn2Own Berlin 2026（2026/05 結束），研究員拿走 130 萬美金，靠的是對每個目標系統準備精確的 threat model。  
**那些研究員給自己的「指引」就是這個等級——先定義成功條件，再找最短路徑實現它。**

---

## 七、繳交說明

請依 `lab-report-template.md` 格式，以**繁體中文**撰寫，**每人一份**。

| 項目 | 要求 |
|------|------|
| 格式 | 依 template 填寫，存成 `.docx` |
| 截圖 | 截圖 1-A、1-B、1-C、2-A、2-B、2-C、3-A、3-B 必附 |
| 檔名 | `W13_Code_Smell_學號_姓名.docx` |
| 截止 | 上課當週週日 23:59 |

**評分方式**：有繳、截圖完整即可得分。

Lab 1、Lab 2、Lab 3 的截圖（1-A、1-B、1-C、2-A、2-B、2-C、3-A、3-B）**缺任何一張不給分**。

---

## 八、期末 Pen-test 報告連結

本週 lab 產出直接對應期末報告的**附錄 A：AI Agent 使用紀錄**。

```
附錄 A：opencode 使用紀錄

A.1 Lab 1 方法論（模糊指引下的 code smell 盤點）
A.2 Lab 2 方法論（agent 對未知 CVE 的盲區評估）
A.3 Lab 3 方法論（好指引下的重寫，smell 減少比較）
A.4 滲透測試中的應用：
    - 我用 opencode 對目標程式碼做的第一輪 smell 掃描
    - opencode 抓到 X 個問題，其中 Y 個是真實漏洞
    - opencode 漏掉的 Z 個漏洞，是我怎麼發現的？
```

**附錄 A 等級越高，顯示你對 agent 的使用越成熟——這是期末評分的加分點。**

---

## 九、延伸閱讀

### Code Smell 基礎

- [Martin Fowler — Code Smell (bliki)](https://martinfowler.com/bliki/CodeSmell.html) — 原始定義
- [Refactoring.Guru — Code Smells 完整目錄](https://refactoring.guru/refactoring/smells) — 五大分類互動式說明

### Code Smell × 安全漏洞（學術研究）

- [Gupta, Suri & Vincent (2020) — Code Smells and Vulnerabilities 相關係數 0.93](https://www.ijcaonline.org/archives/volume176/number32/31405-2020920362/)
- [Kambhampati et al. (2024) — JavaScript Security Code Smells (24 種，含 CWE 對應)](https://arxiv.org/abs/2411.19358)
- [Examining the Relationship of Code and Architectural Smells with Vulnerabilities (2020)](https://arxiv.org/abs/2010.15978) — 9 個開源專案、561 版本分析

### AI 生成程式碼的安全性

- [Security Weaknesses of Copilot-Generated Code (2023)](https://arxiv.org/abs/2310.02059) — 27.3% 含安全弱點
- [Siddiq et al. (SCAM 2022) — Code Smells in Transformer-Based Code Generation](https://zenodo.org/records/7049118) — Copilot 引入 18 種 smell
- [Schreiber & Tippe (2024) — Security Vulnerabilities in AI-Generated Code: Large-Scale Analysis](https://arxiv.org/abs/2510.26103) — 7,703 份 AI 程式碼跨四種工具

### CERT C 與 CWE

- [SEI CERT C Coding Standard](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/)
- [CWE Top 25 (MITRE)](https://cwe.mitre.org/top25/)
- [OWASP Top 10:2025](https://owasp.org/Top10/)

### 本週時事

- [Dirty Frag CVE-2026-43284 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-43284)
- [V4bel/dirtyfrag — PoC repo（含 demo GIF）](https://github.com/V4bel/dirtyfrag)
- [Grafana TanStack 供應鏈攻擊 — Grafana 官方說明](https://grafana.com/blog/grafana-labs-security-update-latest-on-tanstack-npm-supply-chain-ransomware-incident/)
- [Grafana TanStack 供應鏈攻擊 — BleepingComputer](https://www.bleepingcomputer.com/news/security/grafana-breach-caused-by-missed-token-rotation-after-tanstack-attack/)
- [7-Eleven Salesforce 外洩確認 — BleepingComputer](https://www.bleepingcomputer.com/news/security/7-eleven-confirms-data-breach-claimed-by-the-shinyhunters-gang/)
- [Pwn2Own Berlin 2026 結果 — ZDI](https://www.zerodayinitiative.com/blog/)

### 工具

- [semgrep/skills — Agent Skills for Security](https://github.com/semgrep/skills)
- [林柏青，Network and System Security Lab — 中正大學](https://www.cs.ccu.edu.tw/~pclin/) — 本週 C 語言安全程式設計範例來源
