import socket
import threading
import json
import sys
from datetime import datetime

class Client:
    def __init__(self, server_ip, server_port, nickname, client_id):
        self.server_ip = server_ip
        self.server_port = server_port
        self.nickname = nickname
        self.client_id = client_id
        self.start_time = get_time()
        self.sent = 0
        self.received = 0
        self.char_sent = 0
        self.char_recv = 0

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
        except:
            print("ERR - Unable to connect to server.")
            sys.exit(1)

        print(f"ChatClient started with server IP: {self.server_ip}, port: {self.server_port}, nickname: {self.nickname}, client ID: {self.client_id}, Date/Time: {self.start_time}")
        self.send_initial()

        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_loop()

    def send_initial(self):
        initial_msg = {
            "type": "nickname",
            "nickname": self.nickname,
            "clientID": self.client_id,
            "timestamp": self.start_time
        }
        self.sock.send(json.dumps(initial_msg).encode())

    def receive_messages(self):
        while True:
            try:
                msg = self.sock.recv(1024).decode()
                if not msg:
                    break
                data = json.loads(msg)

                if data["type"] == "error":
                    print(data["message"])
                    self.sock.close()
                    sys.exit(1)

                if data["type"] == "broadcast":
                    timestamp = data["timestamp"]
                    nickname = data["nickname"]
                    message = data["message"]
                    print(f"{timestamp} :: {nickname}: {message}")
                    self.received += 1
                    self.char_recv += len(message)

            except:
                break

    def send_loop(self):
        while True:
            msg = input()
            if msg.strip().lower() == "disconnect":
                self.sock.send(json.dumps({
                    "type": "disconnect",
                    "nickname": self.nickname,
                    "clientID": self.client_id
                }).encode())
                break

            ts = get_time()
            data = {
                "type": "message",
                "nickname": self.nickname,
                "message": msg,
                "timestamp": ts
            }
            self.sock.send(json.dumps(data).encode())
            self.sent += 1
            self.char_sent += len(msg)

        end_time = get_time()
        print(f"Summary: start: {self.start_time}, end: {end_time}, msg sent:{self.sent}, msg rcv:{self.received}, char sent:{self.char_sent}, char rcv:{self.char_recv}")
        self.sock.close()

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(f"ERR - arg {len(sys.argv)}")
        sys.exit(1)

    host = sys.argv[1]
    try:
        ip = socket.gethostbyname(host)
    except:
        print("ERR - arg 1")
        sys.exit(1)

    port = int(sys.argv[2]) if sys.argv[2].isdigit() and int(sys.argv[2]) < 65536 else -1
    if port < 0:
        print("ERR - arg 2")
        sys.exit(1)

    nickname = sys.argv[3]
    client_id = sys.argv[4]

    Client(ip, port, nickname, client_id)
