import socket

# 伺服器 IP 與埠號
SERVER_IP = '127.0.0.1'  # 本地測試可用 127.0.0.1
SERVER_PORT = 21  # FTP 標準埠

def ftp_client():
    try:
        # 創建 Socket 連線
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        print(f"[+] 連線到 FTP 伺服器 {SERVER_IP}:{SERVER_PORT}")

        # 接收 FTP 伺服器的回應
        response = s.recv(1024)
        print(f"伺服器回應: {response.decode(errors='ignore')}")

        # 傳送 USER 命令（正常用戶名稱）
        user_command = "USER testuser\r\n"
        s.send(user_command.encode())
        response = s.recv(1024)
        print(f"伺服器回應: {response.decode(errors='ignore')}")

        # 傳送 PASS 命令（密碼）
        pass_command = "PASS testpassword\r\n"
        s.send(pass_command.encode())
        response = s.recv(1024)
        print(f"伺服器回應: {response.decode(errors='ignore')}")

        # 關閉連線
        s.close()
        print("[-] 與伺服器的連線已關閉")

    except Exception as e:
        print(f"[!] 連線錯誤: {e}")

if __name__ == "__main__":
    ftp_client()
