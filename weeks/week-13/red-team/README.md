# Red Team — Week 13

## 攻擊方視角

### 檔案說明

| 檔案 | 用途 |
|------|------|
| `dirty-frag-educational.c` | CVE-2026-43284（Dirty Frag）教育用 exploit 片段 — Linux kernel page cache race condition 導致 COW bypass，非特權使用者可寫入唯讀檔案提權至 root |
| `lab1_verify_password.c` | 含有 4 項 CERT C 違規的脆弱密碼驗證程式 — 紅隊可用於示範 buffer overflow（STR31-C）、timing attack（MSC41-C）、硬編碼憑證（CWE-798）等攻擊手法 |

### 紅隊流程（Lab 對應）

```
Lab 1 → 找出脆弱程式碼中的攻擊面（gets buffer overflow）
Lab 2 → 分析 Dirty Frag 的 race condition 提權路徑
         TOCTOU → COW bypass → 寫入 /etc/passwd → root shell
```

### 攻擊樹（Dirty Frag CVE-2026-43284）

```
非特權使用者
  └─ 傳送特製網路封包（觸發 fragment race condition）
      └─ page cache 競爭寫入
          └─ COW bypass（繞過寫時複製）
              └─ 寫入唯讀檔案（如 /etc/passwd）
                  └─ root shell
```
