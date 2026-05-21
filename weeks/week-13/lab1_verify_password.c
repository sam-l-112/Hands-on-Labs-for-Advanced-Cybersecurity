/*
 * Lab 1 — 模糊指引下的實作（含 security smell）
 * 測試全過，但有多項 CERT C 違規
 */

#include <assert.h>
#include <stdio.h>
#include <string.h>

#define PASSWORD "Sys!stemCrack"
#define MAX_BUF 20

int verify_password(void);

/* 測試案例 */
void test_correct_password_returns_1(void) {
    printf("請輸入正確密碼（%s）...\n", PASSWORD);
    int result = verify_password();
    assert(result == 1);
}

void test_wrong_password_returns_0(void) {
    printf("請輸入錯誤密碼...\n");
    int result = verify_password();
    assert(result == 0);
}

void test_empty_input_returns_0(void) {
    printf("請輸入空字串（直接按 Enter）...\n");
    int result = verify_password();
    assert(result == 0);
}

int main(void) {
    printf("=== Lab 1 — TDD 功能測試 ===\n\n");

    test_correct_password_returns_1();
    printf("[PASS] 正確密碼 → 1\n");

    test_wrong_password_returns_0();
    printf("[PASS] 錯誤密碼 → 0\n");

    test_empty_input_returns_0();
    printf("[PASS] 空字串 → 0\n");

    printf("\n所有測試通過！\n");
    printf("⚠️  但程式安全嗎？請對照 CERT C cheatsheet 檢查。\n");
    return 0;
}

int verify_password(void) {
    char buf[MAX_BUF];

    printf("Password: ");
    gets(buf);

    if (strcmp(buf, PASSWORD) == 0) {
        return 1;
    }
    return 0;
}
