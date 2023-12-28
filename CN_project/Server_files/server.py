import socket
import os

# Config
import struct
import sys

IP = "127.0.0.1"
PORT = 2000
BUFFER_SIZE = 1024
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((IP, PORT))
socket.listen(5)
print(f"\nFTP server is online on {IP}:{PORT}!\n")
conn, addr = socket.accept()

print("\nConnected to by address: {}".format(addr))


import os
import datetime

def list_files():
    print("Listing files...")
    listing = os.listdir(os.getcwd())
    conn.send(len(listing).to_bytes(4, byteorder='big'))
    for i in listing:
        conn.send(len(i).to_bytes(4, byteorder='big'))
        conn.send(i.encode())
        conn.send(os.path.getsize(i).to_bytes(4, byteorder='big'))
        file_creation_time = os.path.getctime(i)
        file_creation_time_str = datetime.datetime.fromtimestamp(file_creation_time).strftime('%Y-%m-%d %H:%M:%S')
        conn.send(file_creation_time_str.encode())
        conn.recv(BUFFER_SIZE)
    print("Successfully sent file listing")
    return



while True:
    data = conn.recv(BUFFER_SIZE).decode()
    print(f"\nReceived: {format(data)}")
    if data == "LIST":
        list_files()
    if data == "QUIT":
        break
    else:
        pass
    data = None




