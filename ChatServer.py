import socket
import threading
import json
import sys
from datetime import datetime
import time

### GLOBAL VARIABLES ###
clients = {}
nicknames = set()

# handles broadcasting message the server recieves to all connected clients
def broadcast(message, senderSock):
    for clientSock in clients:
        if clientSock != senderSock:
            try:
                clientSock.send(message)
            except:
                clientSock.close()

# handler for managing the live server systems
def handle(clientSock, addr):
    try:
        init_msg = clientSock.recv(1024).decode()
        data = json.loads(init_msg)

        # only progresses further if the data loaded is of the type 'nickname'
        if data["type"] == "nickname":
            nickname = data["nickname"]
            client_id = data["clientID"]
            timestamp = data["timestamp"]

            # will handle any nickname conflicts (only for exact copies)
            if nickname in nicknames:
                err = { "type": "error", "message": "Nickname is already in use. Please choose a different one." }
                clientSock.send(json.dumps(err).encode())
                clientSock.close()
                return

            # prepares the client with all needed information
            clients[clientSock] = {
                "addr": addr,
                "nickname": nickname,
                "clientID": client_id
            }
            # adds nickname to the set and displays
            nicknames.add(nickname)

            print(f"{timestamp} :: {nickname}: connected.")
        else:
            clientSock.close()
            return

        while True:
            try:
                # decodes the message recieve from the client and loads it into data as a json
                msg = clientSock.recv(1024).decode()
                if not msg:
                    break
                data = json.loads(msg)

                # manage the type of the data frome the message and what to do
                if data["type"] == "disconnect":
                    break
                elif data["type"] == "message":
                    nickname = data["nickname"]
                    message = data["message"]
                    timestamp = data["timestamp"]
                    ip, port = addr
                    msg_size = len(message)

                    # provides all information on the recieved message and the client
                    print(f"\nReceived: IP:{ip}, Port:{port}, Client-Nickname:{nickname}, ClientID:{clients[clientSock]['clientID']}, Date/Time:{timestamp}, Msg-Size:{msg_size}")

                    # determines what nickname/sockets to broadcast the message to, avoiding the sender
                    recipients = [info["nickname"] for sock, info in clients.items() if sock != clientSock]
                    print(f"Broadcasted: {', '.join(recipients)}")

                    broadcast(json.dumps({
                        "type": "broadcast",
                        "nickname": nickname,
                        "message": message,
                        "timestamp": timestamp
                    }).encode(), clientSock)
            except Exception:
                break

    finally:
        # handles informing the server operator of client disconnect and removes them from the system
        if clientSock in clients:
            nickname = clients[clientSock]["nickname"]
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} :: {nickname}: disconnected.")
            nicknames.remove(nickname)
            del clients[clientSock]
        clientSock.close()

# handles the disconnect message sent to clients
def disconnect(sock):
    try:
        sock.send(json.dumps({
            "type": "disconnect",
            "message": "\nServer is shutting down. Disconnecting..."
        }).encode())
    except:
        pass
        
# used for connecting each client that appears
def connect(sock):
    try:
        sock.settimeout(0.1)
        while True:
            try:
                # creates a thread of each client that joins the server
                clientSock, addr = sock.accept()
                thread = threading.Thread(target=handle, args=(clientSock, addr))
                thread.start()
            # allows for Ctrl+C to properly shut down the server
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully...")
    finally:
        # closes all sockets relating to the server, then to all existing clients 
        sock.close()
        for clientSock in list(clients):
            disconnect(clientSock)
            clientSock.close()
        sys.exit(0)

# main handling system for starting up the server
def main(): 
    # collects the port from system argument
    port = int(sys.argv[1])
    try:
        # sets up the server using socket using the given port
        serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSock.bind(('', port))
        serverSock.listen()
        ip = socket.gethostbyname(socket.gethostname())
        print(f"ChatServer started with server IP: {ip}, port: {port} ...")
    except:
        # informs server operator is port was already in use
        print(f"ERR - cannot create ChatServer socket using port number {port}")
        sys.exit(1)

    for i in range(2):
        # QOL to show person that server is setting up
        time.sleep(1)
        print(".")
    
    connect(serverSock)

if __name__ == "__main__":
    # Initial error catching when setting up the server from its command
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or int(sys.argv[1]) > 65535:
        print("ERR - arg 1")
        sys.exit(1)
    main()
