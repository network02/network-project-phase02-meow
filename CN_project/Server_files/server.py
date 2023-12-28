import socket

# Config
IP = "127.0.0.1"
PORT = 2000
BUFFER_SIZE = 1024
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((IP, PORT))
socket.listen(5)
print(f"\nFTP server is online on {IP}:{PORT}!\n")
conn, addr = socket.accept()

print("\nConnected to by address: {}".format(addr))

while True:
    data = conn.recv(BUFFER_SIZE).decode()
    print(f"\nReceived: {format(data)}")
    if data == "QUIT":
        break
    else:
        pass
    data = None
