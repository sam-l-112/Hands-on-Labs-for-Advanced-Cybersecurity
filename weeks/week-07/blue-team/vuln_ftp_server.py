import socket
import threading
import struct

# 伺服器設定
HOST = '0.0.0.0'
PORT = 21  # FTP 標準埠

# 模擬緩衝區（脆弱伺服器）
BUFFER_SIZE = 512  # 設定小的緩衝區，容易產生溢出
vulnerable_buffer = bytearray(BUFFER_SIZE)

# 🛠️ 處理客戶端連線
def handle_client(client_socket, client_address):
    print(f"[+] 來自 {client_address} 的連線")

    # 發送 FTP 服務訊息
    client_socket.send(b"220 Vulnerable FTP Server Ready\r\n")

    try:
        # Receive and process commands in a loop
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"[*] 接收到: {data.decode(errors='ignore')}")

            # 確認 `USER` 命令
            if data.startswith(b"USER"):
                payload = data[5:].strip()  # 提取 `USER` 後面的資料
                
                # 模擬將 `USER` 傳入有漏洞的緩衝區
                if len(payload) > BUFFER_SIZE:
                    print("[-] 發生緩衝區溢出！")
                    crash_address = struct.pack("<I", 0x41414141)
                    vulnerable_buffer[:len(payload)] = payload
                    vulnerable_buffer[-4:] = crash_address
                    raise Exception("模擬伺服器崩潰！")

                client_socket.send(b"331 User name okay, need password.\r\n")
            
            # `PASS` 命令
            elif data.startswith(b"PASS"):
                client_socket.send(b"230 Login successful.\r\n")

            else:
                client_socket.send(b"500 Unknown command.\r\n")

    except Exception as e:
        print(f"[-] 伺服器崩潰: {e}")
        client_socket.close()
        return

    client_socket.close()
    print(f"[-] 與 {client_address} 的連線已關閉")

# 啟動伺服器
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[+] FTP 伺服器啟動，監聽 {HOST}:{PORT} ...")

    while True:
        client_socket, client_address = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    start_server()
