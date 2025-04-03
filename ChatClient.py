import socket
import threading
import json
import sys
from datetime import datetime

### GLOBAL VARIABLES ###
msg_sent = 0
msg_rcv = 0
char_sent = 0
char_rcv = 0
start_time = ""
nickname = ""
client_id = ""
client_sock = None
running = True

# function defined for getting datetime
def get_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# handles recieving messaages from the server
def receive():
    global msg_rcv, char_rcv, running
    while True:
        try:
            data = client_sock.recv(1024).decode()
            if not data:
                break
            msg = json.loads(data)
            # print(msg["type"])

            ### MESSAGE TYPE HANDLERS ###

            # disconnects and shut down client if message type if 'error'
            if msg["type"] == "error":
                print(msg["message"])
                disconnect()
                sys.exit(1)

            # broadcasts the recieved message to this client  if message type is broadcast
            elif msg["type"] == "broadcast":
                print(f"{msg['timestamp']} :: {msg['nickname']}: {msg['message']}")
                msg_rcv += 1
                char_rcv += len(msg["message"])

            # disconnects from the server 
            elif msg["type"] == "disconnect":
                print(msg["message"])
                running = False
                disconnect()

        except:
            break

# handles sending messages to the server
def send():
    global msg_sent, char_sent, running
    try:
        while running:
            # gets input from the user of the client
            message = input()

            # checks for the exact word 'disconnect' as a input from the user of this client
            if message.strip().lower() == "disconnect":
                running = False
                disconnect()
                break

            # gathers information needed for sending the json messege
            timestamp = get_time()
            chat_msg = {
                "type": "message",
                "nickname": nickname,
                "message": message,
                "timestamp": timestamp
            }
            # stops error being thrown is client is kicked from server by the server
            if not running: break 

            # sends the message and increments statistics based on the message amount and length
            client_sock.send(json.dumps(chat_msg).encode())
            msg_sent += 1
            char_sent += len(message)
    except KeyboardInterrupt:
        running = False
        disconnect()

# handles disconnecting from the server
def disconnect():
    global client_sock

    # preapres message and tries to send disconnect confirmation to server
    dis_msg = {
        "type": "disconnect",
        "nickname": nickname,
        "clientID": client_id
    }
    try:
        client_sock.send(json.dumps(dis_msg).encode())
    except: # on a fail just ignore
        pass

    # provide the user with summary information on their time in the server on all of the statistical information saved
    end_time = get_time()
    print(f"\nSummary: start: {start_time}, end: {end_time}, msg sent:{msg_sent}, msg rcv:{msg_rcv}, char sent:{char_sent}, char rcv:{char_rcv}")
    client_sock.close()
    sys.exit(0)

# main handler for client setup with a specific server
def main():
    global nickname, client_id, client_sock, start_time

    # checking for basic errors in the arguments provided when starting up the client
    if len(sys.argv) != 5:
        print("ERR - arg 1" if len(sys.argv) < 2 else f"ERR - arg {len(sys.argv)}")
        sys.exit(1)

    # given a proper start-up command, sets all information for connecting to the server
    host = sys.argv[1]
    port = int(sys.argv[2]) if sys.argv[2].isdigit() else -1
    nickname = sys.argv[3]
    client_id = sys.argv[4]

    # error check for valid port
    if port < 0 or port > 65535:
        print("ERR - arg 2")
        sys.exit(1)

    # error check for valid ip
    try:
        ip = socket.gethostbyname(host)
    except:
        print("ERR - arg 1")
        sys.exit(1)

    # informs the client a sucessful connection with information on it and informs that they can chat now
    start_time = get_time()
    print(f"ChatClient started with server IP: {ip}, port: {port}, nickname: {nickname}, client ID: {client_id}\nEnter message:\n")
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((ip, port))

    # sends a message to the server informing it who it is for server maintenance
    init_msg = {
        "type": "nickname",
        "nickname": nickname,
        "clientID": client_id,
        "timestamp": start_time
    }
    client_sock.send(json.dumps(init_msg).encode())

    # starts the clients thread from server acceptance and initiates the send function
    threading.Thread(target=receive, daemon=True).start()
    send()

if __name__ == "__main__":
    main()
