## 螢幕擷取範例 1：Console OOB 錯誤

**何時擷取**：點擊「立即更新 iOS 18.7」按鈕後，立即開啟開發者工具 (F12) → Console 標籤

**應顯示內容**：
- 紅色錯誤訊息：`!!! 【DarkSword 漏洞現象】Out-of-Bounds Read/Write 觸發 !!!`
- 第二行：`相鄰記憶體資料已洩漏 → 請檢查 console`
- 可能的堆疊追蹤顯示在 `vulnerableUpload` 函數中
- 時間戳記（可選）

**說明**：此圖證明學生成功觸發了 Out-of-Bounds 讀寫漏洞，是 exploit 第一步的視覺化回饋。

**擷取提示**：
- 確保視窗寬度足以顯示完整錯誤訊息，避免截斷
- 可使用瀏覽器內建的「擷取螢幕畫面」功能或外部工具（如 Snagit、截圖與草圖）
- 建議儲存為 PNG 格式，檔名建議：`screenshot_console_oob.png`