import json
import socket
import threading
import sys
from datetime import datetime

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}  # client socket -> {nickname, clientID}
        self.nicknames = set()

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            ip = socket.gethostbyname(socket.gethostname())
            print(f"ChatServer started with server IP: {ip}, port: {self.port} ...")
        except socket.error:
            print(f"ERR - cannot create ChatServer socket using port number {self.port}")
            sys.exit(1)

    def broadcast_message(self, message, sender_sock=None):
        receivers = []
        for client_sock in self.clients:
            if client_sock != sender_sock:
                try:
                    client_sock.send(message)
                    receivers.append(self.clients[client_sock]["nickname"])
                except:
                    self.disconnect_client(client_sock)
        if receivers:
            print(f"Broadcasted: {', '.join(receivers)}")

    def handle_client(self, client_sock, addr):
        try:
            data = json.loads(client_sock.recv(1024).decode())
            if data["type"] != "nickname":
                raise Exception("Invalid initial message")

            nickname = data["nickname"]
            clientID = data["clientID"]
            timestamp = data["timestamp"]

            if nickname in self.nicknames:
                client_sock.send(json.dumps({ "type": "error", "message": "Nickname is already in use. Please choose a different one." }).encode())
                client_sock.close()
                return

            self.clients[client_sock] = {"nickname": nickname, "clientID": clientID, "addr": addr}
            self.nicknames.add(nickname)
            print(f"{timestamp} :: {nickname}: connected.")

            while True:
                message = client_sock.recv(1024).decode()
                if not message:
                    break

                msg_data = json.loads(message)
                if msg_data["type"] == "disconnect":
                    break
                elif msg_data["type"] == "message":
                    ts = msg_data["timestamp"]
                    msg = msg_data["message"]
                    ip, port = addr
                    size = len(msg)
                    print(f"Received: IP:{ip}, Port:{port}, Client-Nickname:{nickname}, ClientID:{clientID}, Date/Time:{ts}, Msg-Size:{size}")
                    self.broadcast_message(message.encode(), client_sock)

        except Exception:
            pass
        finally:
            self.disconnect_client(client_sock)

    def disconnect_client(self, client_sock):
        if client_sock in self.clients:
            nickname = self.clients[client_sock]["nickname"]
            print(f"{get_time()} :: {nickname}: disconnected.")
            self.nicknames.remove(nickname)
            del self.clients[client_sock]
            client_sock.close()

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or int(sys.argv[1]) > 65535:
        print("ERR - arg 1")
        sys.exit(1)

    port = int(sys.argv[1])
    host = '0.0.0.0'
    server = Server(host, port)

    while True:
        client_sock, addr = server.socket.accept()
        threading.Thread(target=server.handle_client, args=(client_sock, addr)).start()
