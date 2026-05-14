#!/usr/bin/env python3
"""
Week 12 — Lab 3：Transaction State Machine 防禦實作
====================================================
Pack2TheRoot 的根本問題之一：Transaction 的狀態可以被並發操作污染，
造成授權結果與執行時的狀態不一致。

本程式模擬相同的 double-spend 問題（類比套件的雙重安裝）：
  - Transaction.unsafe_execute()：完整實作，展示 race condition
  - Transaction.safe_execute()：骨架，請用 Claude Code / Codex 完成

用法：
  python3 transaction_demo.py --vulnerable   # 觀察 balance 出現負數
  python3 transaction_demo.py --safe         # 測試你的安全實作
"""

import sys
import time
import threading

FLAG = "FLAG{w12_s4f3_st4t3_m4ch1n3_d3f3ns3}"
STRESS_ROUNDS = 1000
WITHDRAW_AMOUNT = 100

# ──────────────────────────────────────────────
# Transaction 類別
# ──────────────────────────────────────────────

class Transaction:
    """
    模擬 PackageKit 的 transaction 狀態機。

    正常流程：
      IDLE → AUTHORIZING → AUTHORIZED → EXECUTING → COMPLETE

    Pack2TheRoot 的問題：
      狀態可以被 backward transition（逆向回退），
      且 flags 在 dispatch 時才讀，而非 authorization 時讀。
    """

    IDLE         = "IDLE"
    AUTHORIZING  = "AUTHORIZING"
    AUTHORIZED   = "AUTHORIZED"
    EXECUTING    = "EXECUTING"
    COMPLETE     = "COMPLETE"

    def __init__(self, initial_balance: int = 100):
        self.balance = initial_balance
        self.state = self.IDLE
        self.lock = threading.Lock()    # 給 safe_execute() 使用
        self.execution_count = 0

    def authorize(self, amount: int) -> bool:
        """模擬 polkit 授權檢查"""
        self.state = self.AUTHORIZING
        if self.balance >= amount:
            self.state = self.AUTHORIZED
            return True
        self.state = self.IDLE
        return False

    # ──────────────────────────────────────────
    # 脆弱版本（完整實作）
    # 問題：state 在 sleep 期間可被另一個 thread 改變，
    #       但程式不重新驗證，直接執行 deduction。
    # ──────────────────────────────────────────

    def unsafe_execute(self, amount: int) -> bool:
        """TOCTOU：state 在 check 和 execute 之間可被競爭修改"""
        if self.state != self.AUTHORIZED:
            return False

        # Race Window：模擬 PackageKit 在 GLib event loop 的處理延遲
        time.sleep(0.001)

        # 問題：沒有重新驗證 state，直接扣款
        self.balance -= amount
        self.state = self.COMPLETE
        self.execution_count += 1
        return True

    # ──────────────────────────────────────────
    # 安全版本骨架（學生實作區）
    # ──────────────────────────────────────────

    def safe_execute(self, amount: int) -> bool:
        with self.lock:
            if self.state != self.AUTHORIZED:
                return False
            time.sleep(0.001)
            if self.state != self.AUTHORIZED:
                return False
            self.balance -= amount
            self.state = self.COMPLETE
            self.execution_count += 1
            return True


# ──────────────────────────────────────────────
# 壓力測試
# ──────────────────────────────────────────────

def run_stress_test(use_safe: bool):
    label = "SAFE" if use_safe else "VULNERABLE"
    print(f"\n{'=' * 60}")
    print(f"  壓力測試模式：{label}")
    print(f"  {STRESS_ROUNDS} 個 thread，每個嘗試提取 {WITHDRAW_AMOUNT}")
    print(f"{'=' * 60}")

    results = []

    for _ in range(STRESS_ROUNDS):
        tx = Transaction(initial_balance=WITHDRAW_AMOUNT)
        threads = []

        # 兩個 thread 同時嘗試 authorize + execute，模擬競爭
        def attempt():
            if tx.authorize(WITHDRAW_AMOUNT):
                if use_safe:
                    tx.safe_execute(WITHDRAW_AMOUNT)
                else:
                    tx.unsafe_execute(WITHDRAW_AMOUNT)

        for _ in range(2):
            t = threading.Thread(target=attempt)
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        results.append((tx.balance, tx.execution_count))

    negative = sum(1 for b, _ in results if b < 0)
    double_exec = sum(1 for _, c in results if c > 1)

    print(f"\n結果：")
    print(f"  總輪數：{STRESS_ROUNDS}")
    print(f"  balance 出現負數：{negative} 次")
    print(f"  執行超過一次：   {double_exec} 次")

    if use_safe and negative == 0 and double_exec == 0:
        print()
        print("╔══════════════════════════════════════════════════╗")
        print(f"  🏁  {FLAG}")
        print("╚══════════════════════════════════════════════════╝")
        print()
        print("✅ 壓力測試通過！safe_execute() 正確防禦了 race condition。")
    elif use_safe:
        print()
        print("❌ 測試未通過，race condition 仍然存在。")
        print("   提示：確認 check 和 execute 在同一個 lock 範圍內。")
    else:
        print()
        print("⚠️  這是預期的脆弱行為，對應 Pack2TheRoot 的 state corruption。")
        print("   現在請修改 safe_execute() 並以 --safe 模式再次執行。")


# ──────────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--help"

    if mode == "--vulnerable":
        run_stress_test(use_safe=False)
    elif mode == "--safe":
        run_stress_test(use_safe=True)
    else:
        print(__doc__)
        print("用法：")
        print("  python3 transaction_demo.py --vulnerable   # 觀察 race condition")
        print("  python3 transaction_demo.py --safe         # 測試安全版本")
