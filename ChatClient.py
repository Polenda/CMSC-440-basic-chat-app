import socket
import threading
import json
import sys
from datetime import datetime

msg_sent = 0
msg_rcv = 0
char_sent = 0
char_rcv = 0
start_time = ""
nickname = ""
client_id = ""
client_sock = None

def get_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def receive():
    global msg_rcv, char_rcv
    while True:
        try:
            data = client_sock.recv(1024).decode()
            if not data:
                break
            msg = json.loads(data)

            if msg["type"] == "error":
                print(msg["message"])
                disconnect()
                sys.exit(1)

            elif msg["type"] == "broadcast":
                print(f"{msg['timestamp']} :: {msg['nickname']}: {msg['message']}")
                msg_rcv += 1
                char_rcv += len(msg["message"])
        except:
            break

def send():
    global msg_sent, char_sent
    try:
        while True:
            message = input()
            if message.strip().lower() == "disconnect":
                disconnect()
                break
            timestamp = get_time()
            chat_msg = {
                "type": "message",
                "nickname": nickname,
                "message": message,
                "timestamp": timestamp
            }
            client_sock.send(json.dumps(chat_msg).encode())
            msg_sent += 1
            char_sent += len(message)
    except KeyboardInterrupt:
        disconnect()

def disconnect():
    global client_sock
    dis_msg = {
        "type": "disconnect",
        "nickname": nickname,
        "clientID": client_id
    }
    try:
        client_sock.send(json.dumps(dis_msg).encode())
    except:
        pass
    end_time = get_time()
    print(f"\nSummary: start: {start_time}, end: {end_time}, msg sent:{msg_sent}, msg rcv:{msg_rcv}, char sent:{char_sent}, char rcv:{char_rcv}")
    client_sock.close()
    sys.exit(0)

def main():
    global nickname, client_id, client_sock, start_time

    if len(sys.argv) != 5:
        print("ERR - arg 1" if len(sys.argv) < 2 else f"ERR - arg {len(sys.argv)}")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if sys.argv[2].isdigit() else -1
    nickname = sys.argv[3]
    client_id = sys.argv[4]

    if port < 0 or port > 65535:
        print("ERR - arg 2")
        sys.exit(1)

    try:
        ip = socket.gethostbyname(host)
    except:
        print("ERR - arg 1")
        sys.exit(1)

    start_time = get_time()
    print(f"ChatClient started with server IP: {ip}, port: {port}, nickname: {nickname}, client ID: {client_id}, Date/Time: {start_time}")

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((ip, port))

    init_msg = {
        "type": "nickname",
        "nickname": nickname,
        "clientID": client_id,
        "timestamp": start_time
    }
    client_sock.send(json.dumps(init_msg).encode())

    threading.Thread(target=receive, daemon=True).start()
    send()

if __name__ == "__main__":
    main()
