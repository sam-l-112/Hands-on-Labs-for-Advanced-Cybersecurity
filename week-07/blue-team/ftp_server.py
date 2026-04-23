import socket
import threading

# 伺服器參數
HOST = '0.0.0.0'  # 允許來自任何 IP 的連接
PORT = 21  # FTP 預設端口

# 處理客戶端連線的函數
def handle_client(client_socket, client_address):
    print(f"[+] 來自 {client_address} 的連線")

    # 發送歡迎訊息
    client_socket.send(b"220 FTP Server Ready\r\n")

    while True:
        try:
            # 接收客戶端數據
            data = client_socket.recv(1024)
            if not data:
                break

            print(f"[*] 接收數據: {data.decode(errors='ignore')}")

            # 檢查是否是 USER 命令
            if data.startswith(b"USER"):
                client_socket.send(b"331 User name okay, need password.\r\n")

            # 檢查是否是 PASS 命令
            elif data.startswith(b"PASS"):
                client_socket.send(b"230 Login successful.\r\n")
                break  # 成功後關閉連接

            else:
                client_socket.send(b"500 Unknown command.\r\n")

        except Exception as e:
            print(f"[-] 錯誤: {e}")
            break

    client_socket.close()
    print(f"[-] 與 {client_address} 的連線已關閉")


def start_server():
    # 創建 socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)  # 允許最多 5 個連接等待

    print(f"[+] 伺服器已啟動，正在監聽 {HOST}:{PORT} ...")

    while True:
        client_socket, client_address = server.accept()
        # 使用多線程處理每個客戶端
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()


if __name__ == "__main__":
    start_server()
