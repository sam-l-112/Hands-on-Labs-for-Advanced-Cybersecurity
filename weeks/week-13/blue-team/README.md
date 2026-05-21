# Blue Team — Week 13

## 防禦方視角

### 檔案說明

| 檔案 | 用途 |
|------|------|
| `cert-c-cheatsheet.md` | CERT C Secure Coding Standard 快速對照表 — STR31-C（緩衝區）、MSC41-C（憑證管理）、CON30-C（競爭條件）、ERR07-C（錯誤處理）等 20+ 規則與 CWE 對應 |
| `lab3_verify_password.c` | 好指引下的安全實作 — 使用 `fgets()`（取代 `gets()`）、SHA-256 hash 比對、constant-time memcmp（防止 timing attack）、256 bytes buffer + 截斷機制 |
| `lab-report-template.md` | 實驗報告模板（含三方比較表、反思欄位） |

### 藍隊流程（Lab 對應）

```
Lab 1 → 用 CERT C cheatsheet 掃 code smell（辨識弱點）
Lab 2 → 驗證 AI 分析結果，對照 NVD/CERT 權威來源
Lab 3 → 將 threat model + 安全測試寫入指引，預防漏洞產生
```

### 防禦矩陣

| 威脅 | CERT 規則 | Lab 3 防禦實作 |
|------|----------|--------------|
| Buffer overflow | STR31-C / STR07-C | `fgets(buf, sizeof(buf), stdin)` |
| Timing attack | MSC41-C | `constant_time_memcmp()` |
| 硬編碼憑證 | MSC41-C / CWE-798 | SHA-256 hash 取代明文 |
| 無錯誤處理 | ERR33-C | 檢查 `fgets()` 回傳值 |
| 資訊洩漏 | ERR07-C / CWE-209 | 錯誤訊息不含內部路徑 |
