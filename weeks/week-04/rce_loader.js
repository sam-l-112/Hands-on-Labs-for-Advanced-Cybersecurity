const canvas = document.getElementById('glcanvas');
const gl = canvas.getContext('webgl');

let secretFlag = "flag{d4rksword_l1t3_w3bgl_oob_2026_kali_ctf_" + Math.random().toString(36).slice(2) + "}";

// 故意有 bug 的 WebGL buffer（模擬 DarkSword GPU OOB）
let buffers = [];
for (let i = 0; i < 80; i++) {
    buffers.push(new ArrayBuffer(0x100));
}

function vulnerableUpload(index, data) {
    const view = new Uint8Array(buffers[index % buffers.length]);  // 故意不檢查邊界
    if (index < 0 || index >= buffers.length) {
        console.error("!!! 【DarkSword 漏洞現象】Out-of-Bounds Read/Write 觸發 !!!");
        console.error("相鄰記憶體資料已洩漏 → 請檢查 console");
        // 視覺化損毀：Canvas 畫壞（紅色亂畫）
        gl.clearColor(1, 0, 0, 1);
        gl.clear(gl.COLOR_BUFFER_BIT);
        throw "Memory corruption observed! (Canvas 已損毀)";
    }
    view.set(data);
}

// 學生 exploit 入口
window.startExploit = function() {
    console.log("%cDarkSword-Lite Exploit 開始... 使用 Codex 開發！", "color:red; font-size:16px");
    // 這裡會被 exploit_template.js 覆寫
};