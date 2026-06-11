# Week 17 — 期末報告撰寫

**日期**：2026/06/15–06/21
**時長**：3 小時（180 分鐘）
**繳交截止**：民國 115 年 6 月 21 日 23:59（上傳 ee-class）

[TOC]

---

## 一、報告要求總覽

### 主題與標的

**報告主題：** Web 應用程式弱點檢測實作報告

**受測標的（擇一或兩者皆做）：**
- DVWA（`kaakaww/dvwa-docker`，本機 Docker）
- OWASP Juice Shop（`bkimminich/juice-shop`，本機 Docker）

### 繳交內容

| # | 項目 | 說明 |
|---|------|------|
| 1 | 報告書（PDF） | 依指定章節結構撰寫，25–30 頁（不含封面、目錄） |
| 2 | 每個漏洞 | 位置 + 重現步驟 + payload + 截圖，缺一不計分 |
| 3 | Juice Shop | 每清除 1 個 challenge，附 Scoreboard 截圖 |

### 格式要求

| 項目 | 規定 |
|------|------|
| 字型 | 標楷體 / 新細明體 12pt |
| 行距 | 1.5 |
| 頁碼 | 必備 |
| 目錄 | 必備 |
| 頁首 / 頁尾 | 必備 |
| 頁數 | 25–30 頁（不含封面、目錄） |
| 格式 | PDF 繳交 |

---

## 二、評分標準

### 漏洞有效認定（採計前提）

> 一個發現須同時具備 **位置 + 重現步驟 + payload + 截圖**，才計為 1 個有效漏洞。缺少任一項，不予採計。
>
> Juice Shop 每清除 1 個 challenge（附計分板截圖）＝ 1 個有效漏洞。

### 計分方式

| 項目 | 分數 |
|------|------|
| **基本門檻**：完成 5 個有效漏洞 | 60 分 |
| **數量加分**：第 6 個起，每增加 1 個 | +4 分 |
| （最多採計至第 12 個，即最多 +28 分） | 最高 88 分 |
| **品質加分**（見下方） | 最多 12 分 |
| **滿分** | **100 分** |

### 品質加分（12 分）

| 項目 | 分數 |
|------|------|
| 風險等級涵蓋多元（Critical / High / Medium / Low 都有） | 4 分 |
| 重現步驟與截圖清晰，可由他人獨立複現 | 4 分 |
| 修補建議具體可行（非泛泛而論） | 4 分 |

### 建議達標策略

```
DVWA  → 4–5 個經典漏洞（SQLi、Command Injection、File Upload、XSS、Brute Force）
Juice Shop → 6–7 個低星 challenge（1–3 星），每個附 Scoreboard 截圖
合計 10–12 個，刻意做出 Critical / High / Medium / Low 的風險分布
```

---

## 三、報告章節結構（指定目錄）

```
封面
目錄
一、授權與免責聲明
二、測試環境說明
三、測試方法論
四、漏洞發現
    4.1 漏洞 #01 — （名稱）
    4.2 漏洞 #02 — （名稱）
    ...
五、修補建議彙整
六、結論
七、參考資料
附錄（截圖、Scoreboard、證據保存清單 EVIDENCE_INDEX）
```

詳細格式見 [final-report-template.md](final-report-template.md)。

---

## 四、今天的時間配置

| 時間 | 工作 |
|------|------|
| 0:00–0:20 | 環境確認，靶機啟動，報告模板準備 |
| 0:20–0:60 | 繼續打靶機，補齊漏洞截圖 |
| 1:00–1:30 | 撰寫每個漏洞的「重現步驟 + payload」文字 |
| 1:30–1:55 | 撰寫「授權聲明 + 測試環境 + 修補建議 + 結論」 |
| 1:55–2:30 | 整合進 Word，排版（字型、行距、頁碼、頁首/頁尾） |
| 2:30–2:50 | 自我驗收 Checklist |
| 2:50–3:00 | 輸出 PDF + 上傳確認 |

---

## 五、各漏洞必備四要素

每個漏洞章節都要有這四樣，**缺一整個漏洞不計分**：

### 1. 位置（Location）

說明在哪裡發現這個漏洞：

```
受影響 URL：http://localhost/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit
受影響參數：id
```

### 2. 重現步驟（Reproduction Steps）

讓助教能照著做：

```
1. 開啟瀏覽器，前往 http://localhost/dvwa/vulnerabilities/sqli/
2. 在 User ID 欄位輸入以下 payload
3. 點擊 Submit，觀察回應
```

### 3. Payload

直接貼指令或輸入值：

```sql
1' OR '1'='1'--
```
```bash
curl -s "http://localhost/dvwa/vulnerabilities/sqli/?id=1'+OR+'1'='1'--+&Submit=Submit" \
  -H "Cookie: PHPSESSID=xxx; security=low"
```

### 4. 截圖佐證（Screenshot）

- 截圖要清楚顯示 payload 的輸入與伺服器的回應
- Juice Shop challenge 截圖要包含 **Scoreboard 頁面**（URL 顯示 `/#/score-board`）且該 challenge 旁有 🏆

---

## 六、證據保存（沿用 Week 14 鑑識證據鏈）

期末報告不只是「打得到」，還要「證明得了」。本次報告的每個漏洞，**證據都要沿用 [Week 14](../week-14/README.md) 建立的 NIST SP 800-86 鑑識證據鏈作法**——截圖不是孤立的圖片，而是可追溯、可驗證完整性的證據。

### 6.1 為什麼要保存證據（[NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final)）

> 一份只有截圖、沒有時間戳與雜湊的證據，在真實 pentest 報告裡是站不住腳的——你無法證明它「什麼時候、對哪個目標、用什麼指令」取得，也無法證明它事後沒被竄改。

沿用 Week 14 的 **5W1H + Integrity** 框架，每份證據都要能回答：

| 問題 | 要保存的內容 | 對應 NIST |
|------|------------|----------|
| **When** | 取得時間（UTC）、系統時區 | Traceability |
| **Where** | URL、參數、Docker container ID / image SHA | Traceability |
| **Who** | 操作者、工具名稱與版本 | Traceability |
| **How** | 完整指令、payload、wordlist 名稱 | Reproducibility |
| **What** | 原始回應、截圖、log 內容 | Documentation |
| **Integrity** | SHA-256、含 timestamp 的不可變檔名、`EVIDENCE_INDEX.md` | Integrity |

### 6.2 直接重用 Week 14 的 `evidence_<學號>.sh`

Week 14 課前已要求每人依 [evidence-guidelines.md](../week-14/evidence-guidelines.md) 自製一份 `evidence_<學號>.sh`（提供 `ev_start` / `ev_cmd` / `ev_end`）。**期末報告打靶時請直接 source 同一份腳本**，不需重寫：

```bash
export PENTEST_DIR=~/labs/final
mkdir -p "$PENTEST_DIR"/{evidence,logs,reports}
source ~/labs/week14/evidence_<學號>.sh

# 每打一個漏洞，跑一輪 ev_start → ev_cmd → 工具 → ev_end
ev_start "dvwa_sqli" "http://localhost/dvwa/vulnerabilities/sqli/" "final report - SQLi"
ev_cmd "sqlmap -u 'http://localhost/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit' --cookie='PHPSESSID=xxx; security=low' --batch --dump --output-dir $EV_DIR/sqlmap_out"
sqlmap -u 'http://localhost/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit' \
  --cookie='PHPSESSID=xxx; security=low' --batch --dump --output-dir "$EV_DIR/sqlmap_out"
ev_end
```

`ev_end` 會自動：對 `$EV_DIR` 內所有檔案計算 SHA-256、補上結束時間、在 `logs/EVIDENCE_INDEX.md` 附加一列。

> **截圖也是證據**：把每個漏洞的截圖（含 Juice Shop Scoreboard）存進對應的 `$EV_DIR/`，這樣截圖會一起被 `ev_end` 算進 SHA-256，與該次操作的時間戳、指令綁在一起。

### 6.3 報告裡要怎麼呈現

1. **每個漏洞節**：在「截圖佐證」下方加一行證據對應，例如
   `證據目錄：03_dvwa_sqli_20260615_142233／SHA-256（raw 前16碼）：a3f1b2c4d5e6f789…`
2. **附錄**：把整份 `EVIDENCE_INDEX.md` 貼進報告附錄（見 [final-report-template.md](final-report-template.md) 附錄 D），讓助教能逐筆對照漏洞與證據。
3. **可驗證**：保留 `evidence/` 目錄，必要時助教可用 `sha256sum -c sha256.txt` 驗證證據未被竄改。

> **加分提示**：完整的證據鏈（時間戳 + SHA-256 + EVIDENCE_INDEX）對應「重現步驟與截圖清晰，可由他人獨立複現」的品質加分（4 分）。

---

## 七、Juice Shop Scoreboard 截圖規範

Scoreboard URL：`http://localhost:3000/#/score-board`

截圖需顯示：
1. 瀏覽器網址列（確認是 `/#/score-board`）
2. 已完成的 challenge 旁有 🏆 圖示
3. challenge 名稱清晰可辨

> 若只截攻擊成功的 popup，沒有 Scoreboard 截圖，**不予採計**。

**建議選的 1–3 星 challenge（容易達成）：**

| Challenge | 星數 | 類型 |
|-----------|------|------|
| Score Board | ⭐ | 找到隱藏頁面 |
| DOM XSS | ⭐ | XSS |
| Bonus Payload | ⭐ | XSS |
| Error Handling | ⭐ | 資訊洩漏 |
| Exposed Metrics | ⭐ | 資訊洩漏 |
| Zero Stars | ⭐ | 邏輯漏洞 |
| Login Admin | ⭐⭐ | SQLi |
| Admin Section | ⭐⭐ | 存取控制 |
| View Basket | ⭐⭐ | IDOR |
| Five-Star Feedback | ⭐⭐ | 存取控制 |
| Login Bender | ⭐⭐ | SQLi |
| Password Strength | ⭐⭐ | 弱密碼 |

---

## 八、自我驗收 Checklist

報告輸出 PDF 前，逐項確認：

### 格式

- [ ] 字型：標楷體 / 新細明體 12pt
- [ ] 行距：1.5
- [ ] 有頁碼
- [ ] 有目錄（且與實際章節一致）
- [ ] 有頁首 / 頁尾
- [ ] 正文頁數 25–30 頁（不含封面、目錄）

### 章節結構

- [ ] 一、授權與免責聲明（說明測試於合法自架環境，禁止攻擊外部系統）
- [ ] 二、測試環境說明（OS、Docker image、靶機版本）
- [ ] 三、測試方法論（用了哪些工具、哪些方法）
- [ ] 四、漏洞發現（每個漏洞一節，見下方）
- [ ] 五、修補建議彙整（有優先順序，非複製貼上）
- [ ] 六、結論
- [ ] 七、參考資料

### 每個漏洞

- [ ] 有受影響位置（URL + 參數）
- [ ] 有重現步驟（步驟 1、2、3…）
- [ ] 有 payload（指令或輸入值）
- [ ] 有截圖（顯示 payload 輸入 + 伺服器回應）
- [ ] 有 CVSS 3.1 分數
- [ ] 有 Business Impact（非技術語言）
- [ ] 有修補建議（至少 1 條）
- [ ] 有證據對應（證據目錄名稱 + SHA-256 前 16 碼）

### 證據保存（沿用 Week 14）

- [ ] 打靶時有 source `evidence_<學號>.sh`，每個漏洞跑過 `ev_start → ev_cmd → ev_end`
- [ ] 截圖存進對應 `$EV_DIR/`，與時間戳、指令一起被算入 SHA-256
- [ ] `logs/EVIDENCE_INDEX.md` 每個漏洞都有一列（無空白列、SHA-256 由腳本自動計算）
- [ ] 報告附錄貼上完整 `EVIDENCE_INDEX.md`
- [ ] 保留 `evidence/` 目錄，可用 `sha256sum -c` 驗證

### Juice Shop 專項

- [ ] 每個 challenge 有 Scoreboard 截圖（含 🏆）
- [ ] Scoreboard 截圖網址列顯示 `/#/score-board`

### 法律與學術誠信

- [ ] 報告有授權 / 免責聲明
- [ ] 所有測試僅在自架靶機進行，未測試任何外部系統
- [ ] 內容為個人獨立完成（抄襲、共用依校規處理）

---

## 九、輸出 PDF + 繳交

```
檔名：FINAL_Pentest_學號_姓名.pdf
上傳：ee-class → 進階駭客攻防技術 → 期末作業
截止：民國 115 年 6 月 21 日 23:59
```

---

## 十、注意事項

- 嚴禁攻擊校外或他人真實系統，違者以**零分**計
- 抄襲、共用報告依校規處理
- PDF 無法開啟者視同未繳交
