# 證據保護腳本設計規格書

**課程**：進階道德駭客 Week 14
**性質**：個人作業（課前繳交）
**目標**：依本規格書，自行實作一份 Bash 腳本，用於 Lab 期間的所有證據收集

---

## 一、為什麼要自己寫？

直接使用現成工具，你只知道「怎麼用」；自己實作規格，你才知道「為什麼這樣做」。

NIST SP 800-86 的核心不是工具，而是**思維**：

> *每一份數位證據，都要在取得的當下，立即記錄它的來源、完整性與脈絡。事後補記的證據，在法庭與審計上都不被接受。*

你的腳本就是把這個思維變成可執行的程式碼。

---

## 二、你的腳本必須提供三個函式

### `ev_start <標籤> <目標> <說明>`

**目的**：在執行任何工具前，先把 When / Where / Who 記錄下來。

**最低行為要求**：

1. 在 `$PENTEST_DIR/evidence/` 下建立一個子目錄，命名規則為：

   ```
   <序號>_<標籤>_<UTC時間戳>
   例：02_sqlmap_20260601_083045
   ```

   序號從 `01` 開始，每次呼叫 `ev_start` 自動遞增。

2. 在該子目錄建立 `metadata.json`，**至少**包含以下欄位：

   ```json
   {
     "when": {
       "start_utc": "<ISO 8601，例 2026-06-01T08:30:45Z>",
       "end_utc": null,
       "system_tz": "<時區縮寫>",
       "system_clock": "<date 指令的完整輸出>"
     },
     "where": {
       "target": "<目標 URL 或 IP>",
       "hostname": "<攻擊端主機名稱>",
       "container_id": "<docker ps 取得的 juice-shop container ID，若適用>"
     },
     "who": {
       "operator": "<whoami 輸出>",
       "tool": "<標籤>"
     },
     "how": {
       "command": null,
       "notes": "<說明參數的內容>"
     },
     "what": {
       "raw_output": "raw_output.txt",
       "sha256_manifest": "sha256.txt"
     }
   }
   ```

   `end_utc` 和 `command` 此時填 `null`，由後續函式補上。

3. 將以下兩個環境變數 export 給外部 shell 使用：

   ```bash
   EV_DIR   # 剛建立的子目錄絕對路徑
   EV_RAW   # $EV_DIR/raw_output.txt 的絕對路徑
   ```

4. 在終端機印出確認訊息，至少包含標籤、時間、目標。

---

### `ev_cmd "<完整指令字串>"`

**目的**：在工具執行**前**，記錄 How——完整的指令，包括所有參數與 flag。

**最低行為要求**：

1. 將指令字串寫入 `$EV_DIR/command_log.txt`（可附加，不可覆蓋）。
2. 更新 `metadata.json` 的 `how.command` 欄位為該指令字串。
3. 若 `$EV_DIR` 尚未被 `ev_start` 設定，印出錯誤並 return 1。

---

### `ev_end`

**目的**：工具執行完畢後，立即封存這份證據。

**最低行為要求**：

1. 把當下的 UTC 時間寫入 `metadata.json` 的 `when.end_utc`。
2. 對 `$EV_DIR` 內的**所有檔案**（含 `metadata.json`、`raw_output.txt`、`command_log.txt`）計算 SHA-256，結果寫入 `$EV_DIR/sha256.txt`，格式與 `sha256sum` 的標準輸出相同：

   ```
   <hash>  <filepath>
   ```

3. 在 `$PENTEST_DIR/logs/EVIDENCE_INDEX.md` 的表格中**附加一列**，包含：

   | 欄位 | 內容 |
   |------|------|
   | 序號 | 與 ev_start 相同的兩位數序號 |
   | 標籤 | ev_start 的第一個參數 |
   | 開始時間 UTC | metadata.json 的 when.start_utc |
   | 目標 | metadata.json 的 where.target |
   | 操作者 / 工具 | metadata.json 的 who.operator + who.tool |
   | 指令 | command_log.txt 第一行 |
   | SHA-256（前16碼）| raw_output.txt 的雜湊前 16 個字元 + `...` |

4. 在終端機印出確認訊息，包含結束時間與 sha256.txt 的內容摘要。

---

## 三、選擇性函式（加分）

### `ev_hash "<檔案路徑>"`

對單一檔案計算 SHA-256，並將結果**附加**到 `$EV_DIR/sha256.txt`。
用途：工具產生多個輸出檔時（如 sqlmap output 目錄），逐一補算。

---

## 四、EVIDENCE_INDEX.md 格式規定

你的腳本必須在首次執行時**自動建立**這個檔案（如果不存在），並維護以下 Markdown 表格格式：

```markdown
# Evidence Index

> NIST SP 800-86 compliant evidence log

| # | Label | Start (UTC) | Target | Operator / Tool | Command | SHA-256 (raw) |
|---|-------|-------------|--------|-----------------|---------|---------------|
| 01 | nikto | 2026-06-01T08:10:00Z | http://localhost:3000 | kali / nikto | nikto -h ... | `a3f1b2c4d5e6f789...` |
```

**不允許**的格式：
- 空白列（每次 ev_end 必定附加一列，不得留空）
- 事後手動編輯欄位（SHA-256 必須是腳本自動計算，不得人工填入）

---

## 五、目錄結構驗收標準

完成所有 Lab 後，你的 `$PENTEST_DIR` 應呈現以下結構：

```
pentest/week14/
├── evidence/
│   ├── 01_nikto_20260601_081000/
│   │   ├── metadata.json        ← When/Where/Who/How 完整
│   │   ├── command_log.txt      ← 完整指令
│   │   ├── raw_output.txt       ← 工具原始輸出
│   │   └── sha256.txt           ← sha256sum 格式，可用 -c 驗證
│   ├── 02_sqlmap_20260601_083045/
│   │   └── ...
│   └── ...
├── logs/
│   ├── EVIDENCE_INDEX.md        ← 所有證據的一覽表
│   └── session_*.log            ← script 指令完整記錄
└── reports/
    ├── finding-01-sqli.md
    ├── finding-02-bac.md
    └── finding-03-bruteforce.md
```

---

## 六、自我驗收

上課前可以自己跑以下指令確認腳本正常：

```bash
# 載入腳本
source evidence_<學號>.sh

# 模擬一次完整的證據收集
export PENTEST_DIR=$(mktemp -d)
ev_start "test_tool" "http://localhost:3000" "self-test"
ev_cmd "echo hello > \$EV_RAW"
echo "hello world" > "$EV_RAW"
ev_end

# 手動確認下列三點
sha256sum -c "$EV_DIR/sha256.txt"                          # 應全部 OK
cat "$EV_DIR/metadata.json"                                # 確認欄位齊全
grep "test_tool" "$PENTEST_DIR/logs/EVIDENCE_INDEX.md"     # 確認 Index 有這筆
```

---

## 七、常見錯誤

| 錯誤 | 原因 | 對應 NIST 要求 |
|------|------|----------------|
| SHA-256 在所有 Lab 跑完後才統一計算 | 若中間有檔案被修改，雜湊無法反映原始狀態 | Integrity |
| `metadata.json` 的 `end_utc` 仍為 null | ev_end 沒有補上結束時間 | Traceability |
| `command_log.txt` 記錄的是事後重建的指令，而非執行前的原始指令 | How 欄位必須在執行前記錄 | Reproducibility |
| EVIDENCE_INDEX.md 以手動方式填入 SHA-256 | 雜湊必須由程式自動計算 | Integrity |
| 目錄命名不含時間戳 | 無法還原「什麼時候」收集的 | Traceability |

這些錯誤在課堂 Lab 都會直接顯現——SHA-256 對不上、Index 欄位空白——自己就能發現。

---

## 八、繳交方式

1. 依課程提供的 pentest 報告範本，將三份 Finding 單（SQLi、BAC、暴力破解）整理成一份 **Word 檔**（`.docx`）。
2. 上傳至 **ee-class** 對應作業區，檔名格式：`W14_Pentest_學號_姓名.docx`。
