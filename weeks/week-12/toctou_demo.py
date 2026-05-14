#!/usr/bin/env python3
"""
Week 12 — Lab 2：TOCTOU Race Condition 模擬
============================================
CVE-2026-41651（Pack2TheRoot）的核心問題是 pk-transaction.c 中
check 和 use 之間沒有鎖定狀態，造成 race condition。

本程式用 Python 模擬同樣的模式：
  - vulnerable_daemon()：完整實作，展示脆弱的 check-sleep-use 流程
  - exploit_thread()：骨架，請用 Claude Code / Codex 完成攻擊邏輯
  - safe_daemon()：骨架，請用 Claude Code / Codex 完成安全版本

用法：
  python3 toctou_demo.py --vulnerable   # 觀察脆弱版本
  python3 toctou_demo.py --safe         # 測試你的安全版本
"""

import os
import sys
import time
import threading

# ──────────────────────────────────────────────
# 常數設定
# ──────────────────────────────────────────────

INPUT_FILE = "/tmp/w12_toctou_input.txt"
SAFE_CONTENT = "NORMAL_PACKAGE_REQUEST"
TRIGGER = "PRIVILEGED_PAYLOAD"
RACE_WINDOW = 0.2   # 模擬 GLib event loop 的處理窗口（秒）

FLAG = "FLAG{w12_t0ctou_r4c3_w1n_pack2theroot}"

# ──────────────────────────────────────────────
# 輔助函式
# ──────────────────────────────────────────────

def reset_input():
    """重設 input file 為正常內容"""
    with open(INPUT_FILE, "w") as f:
        f.write(SAFE_CONTENT)


def banner(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

# ──────────────────────────────────────────────
# 脆弱的 daemon（完整實作）
# 模擬 pk-transaction.c 的 InstallFiles() 行為：
#   1. 讀取請求內容（Check）
#   2. 等待 GLib event loop 處理（Race Window）
#   3. 再次讀取並執行（Use）← TOCTOU 就在這裡
# ──────────────────────────────────────────────

def vulnerable_daemon():
    print("[daemon] 收到套件安裝請求")

    # Step 1：Check — 讀取請求，驗證是否安全
    with open(INPUT_FILE, "r") as f:
        content_at_check = f.read()

    if TRIGGER in content_at_check:
        print("[daemon] ✗ 初始檢查失敗，拒絕請求")
        return

    print(f"[daemon] ✓ 授權檢查通過（內容：{content_at_check[:30]}）")
    print(f"[daemon] 等待 event loop 處理（{RACE_WINDOW}s）...")

    # Step 2：Race Window — 模擬 GLib 的 D-Bus message 處理延遲
    time.sleep(RACE_WINDOW)

    # Step 3：Use — 重新讀取並執行（這是 TOCTOU 的核心問題）
    with open(INPUT_FILE, "r") as f:
        content_at_use = f.read()

    if TRIGGER in content_at_use:
        print("[daemon] 🚨 執行了未經授權的特權操作！")
        print()
        print("╔══════════════════════════════════════════════════╗")
        print(f"  🏁  {FLAG}")
        print("╚══════════════════════════════════════════════════╝")
        print()
    else:
        print(f"[daemon] 套件已安裝：{content_at_use[:30]}")


# ──────────────────────────────────────────────
# 攻擊執行緒骨架（學生實作區）
# ──────────────────────────────────────────────

def exploit_thread():
    """
    TODO：完成這個函式，在 Race Window 內替換 INPUT_FILE 的內容。

    目標：讓 vulnerable_daemon() 在 Step 3 讀到 TRIGGER，
          但 Step 1 的檢查已經通過。

    提示：
    - RACE_WINDOW = 0.2 秒，這是你的操作窗口
    - Step 1（Check）完成後才能開始替換
    - 替換時機：在 Check 完成後、Use 執行前
    - 替換方法：把 INPUT_FILE 的內容改成包含 TRIGGER 的字串

    建議使用 Claude Code / Codex 輔助實作。

    參考：在真實的 Pack2TheRoot 中，攻擊者發送兩個非同步 D-Bus
          訊息，第一個帶 SIMULATE flag（通過授權），第二個帶惡意套件。
          GLib 的 event loop 優先順序保證兩個都在 callback 前處理。
    """
    # TODO：實作攻擊邏輯
    pass


# ──────────────────────────────────────────────
# 安全版 daemon 骨架（學生實作區）
# ──────────────────────────────────────────────

def safe_daemon():
    """
    TODO：修復 vulnerable_daemon() 的 TOCTOU 問題。

    目標：讓 exploit_thread() 無法改變執行結果。

    修復方向（三選一）：
    A. 讀取一次後不重複讀取（使用同一個 content_at_check 變數執行）
    B. 使用 threading.Lock() 讓 check 和 use 成為原子操作
    C. 在 Use 前重新驗證內容是否與 Check 時一致

    建議使用 Claude Code / Codex 輔助實作。
    """
    print("[daemon] 收到套件安裝請求")
    # TODO：實作安全版本
    pass


# ──────────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────────

def run_mode(daemon_fn, label: str):
    banner(label)
    reset_input()

    t_daemon = threading.Thread(target=daemon_fn, name="daemon")
    t_attack = threading.Thread(target=exploit_thread, name="attacker")

    t_daemon.start()
    t_attack.start()

    t_daemon.join()
    t_attack.join()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--help"

    if mode == "--vulnerable":
        run_mode(vulnerable_daemon, "模式：VULNERABLE（check-sleep-use，無鎖定）")

    elif mode == "--safe":
        run_mode(safe_daemon, "模式：SAFE（你的安全實作）")

    else:
        print(__doc__)
        print("用法：")
        print("  python3 toctou_demo.py --vulnerable   # 觀察脆弱版本")
        print("  python3 toctou_demo.py --safe         # 測試安全版本")
