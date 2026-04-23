import random
import string


def generate_random_flag():
    """生成隨機旗標，格式為 flag{d4rksword_l1t3_w3bgl_oob_2026_kali_ctf_xxxxxxxx}"""
    # 生成8個隨機十六進制字符
    random_suffix = "".join(random.choices(string.hexdigits.lower(), k=8))
    flag = f"flag{{d4rksword_l1t3_w3bgl_oob_2026_kali_ctf_{random_suffix}}}"
    return flag


def generate_multiple_flags(count=5):
    """生成多個隨機旗標"""
    flags = []
    for i in range(count):
        flags.append(generate_random_flag())
    return flags


if __name__ == "__main__":
    print("=== DarkSword-Lite CTF 隨機旗標生成器 ===")
    print()

    # 生成單個旗標
    single_flag = generate_random_flag()
    print(f"單個旗標: {single_flag}")
    print()

    # 生成多個旗標（預設5個）
    print("多個旗標範例:")
    flags = generate_multiple_flags(5)
    for i, flag in enumerate(flags, 1):
        print(f"{i}. {flag}")
    print()

    # 使用說明
    print("使用說明:")
    print("1. 複製生成的旗標")
    print("2. 替換 rce_loader.js 中的 secretFlag 變數值")
    print(
        '3. 例如: let secretFlag = "flag{d4rksword_l1t3_w3bgl_oob_2026_kali_ctf_abc123}";'
    )
    print()
    print("提示: 每次執行此腳本都會產生不同的旗標！")
