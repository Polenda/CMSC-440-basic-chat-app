import socket
import threading
import json
import sys
from datetime import datetime
import time

clients = {}
nicknames = set()

def broadcast(message, sender_sock):
    for client_sock in clients:
        if client_sock != sender_sock:
            try:
                client_sock.send(message)
            except:
                client_sock.close()

def handle(client_sock, addr):
    try:
        init_msg = client_sock.recv(1024).decode()
        data = json.loads(init_msg)

        if data["type"] == "nickname":
            nickname = data["nickname"]
            client_id = data["clientID"]
            timestamp = data["timestamp"]

            if nickname in nicknames:
                err = { "type": "error", "message": "Nickname is already in use. Please choose a different one." }
                client_sock.send(json.dumps(err).encode())
                client_sock.close()
                return

            clients[client_sock] = {
                "addr": addr,
                "nickname": nickname,
                "clientID": client_id
            }
            nicknames.add(nickname)

            print(f"{timestamp} :: {nickname}: connected.")
        else:
            client_sock.close()
            return

        while True:
            try:
                msg = client_sock.recv(1024).decode()
                if not msg:
                    break
                data = json.loads(msg)

                if data["type"] == "disconnect":
                    break
                elif data["type"] == "message":
                    nickname = data["nickname"]
                    message = data["message"]
                    timestamp = data["timestamp"]
                    ip, port = addr
                    msg_size = len(message)

                    print(f"\nReceived: IP:{ip}, Port:{port}, Client-Nickname:{nickname}, ClientID:{clients[client_sock]['clientID']}, Date/Time:{timestamp}, Msg-Size:{msg_size}")

                    recipients = [info["nickname"] for sock, info in clients.items() if sock != client_sock]
                    print(f"Broadcasted: {', '.join(recipients)}")

                    broadcast(json.dumps({
                        "type": "broadcast",
                        "nickname": nickname,
                        "message": message,
                        "timestamp": timestamp
                    }).encode(), client_sock)
            except Exception:
                break

    finally:
        if client_sock in clients:
            nickname = clients[client_sock]["nickname"]
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} :: {nickname}: disconnected.")
            nicknames.remove(nickname)
            del clients[client_sock]
        client_sock.close()

def start_server(port, sock):
    try:
        sock.settimeout(0.1)
        while True:
            try:
                client_sock, addr = sock.accept()
                thread = threading.Thread(target=handle, args=(client_sock, addr))
                thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully...")
    finally:
        sock.close()
        for client_sock in list(clients):
            client_sock.close()
        sys.exit(0)

def main():
    port = int(sys.argv[1])
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('', port))
        server_sock.listen()
        ip = socket.gethostbyname(socket.gethostname())
        print(f"ChatServer started with server IP: {ip}, port: {port} ...")
    except:
        print(f"ERR - cannot create ChatServer socket using port number {port}")
        sys.exit(1)

    for i in range(2):
        time.sleep(1)
        print(".")
    
    start_server(port, server_sock)

if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or int(sys.argv[1]) > 65535:
        print("ERR - arg 1")
        sys.exit(1)
    main()
