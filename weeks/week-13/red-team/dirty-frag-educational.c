/*
 * dirty-frag-educational.c — Week 13 Lab 2 教學用片段
 *
 * 這是一個簡化的教學範例，用來示範「頁快取（page cache）競爭條件」的核心概念。
 *
 * 注意：這不是可執行的 exploit，缺少多個必要的 kernel 結構與 helper。
 */

#include <linux/mm.h>       /* page cache operations */
#include <linux/skbuff.h>   /* sk_buff, skb_frag_t */

/*
 * fragment_process() 負責處理網路封包的 skb fragment。
 */
static int fragment_process(struct sk_buff *skb, int offset)
{
    skb_frag_t *frag;
    struct page *page;
    void *vaddr;
    int i;

    /* 走訪所有 fragments */
    for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
        frag = &skb_shinfo(skb)->frags[i];
        page = skb_frag_page(frag);

        vaddr = kmap_atomic(page);
        memset(vaddr + skb_frag_off(frag), 0, skb_frag_size(frag));

        kunmap_atomic(vaddr);
    }

    return 0;
}

