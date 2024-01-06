import socket
import os
import datetime

# Config
import struct

IP = "127.0.0.1"
PORT = 2001
BUFFER_SIZE = 1024
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((IP, PORT))
socket.listen(5)
print(f"\nFTP server is online on {IP}:{PORT}!\n")
conn, addr = socket.accept()

print("\nConnected to by address: {}".format(addr))

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


def delete_file():
    conn.sendall(b"1")
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length).decode()
    if os.path.isfile(file_name):
        conn.sendall(struct.pack("i", 1))
    else:
        conn.sendall(struct.pack("i", -1))
        return None
    confirm_delete = conn.recv(BUFFER_SIZE).decode()
    if confirm_delete == "Y":
        try:
            os.remove(file_name)
            conn.sendall(struct.pack("i", 1))
        except:
            print("Failed to delete {}".format(file_name))
            conn.sendall(struct.pack("i", -1))
    else:
        print("Delete abandoned by the client!")
        return None


def create_directory():
    # Send go-ahead
    conn.sendall(b"1")
    # Get Directory details
    directory_name_length = struct.unpack("h", conn.recv(2))[0]
    print(directory_name_length)
    conn.sendall(b"1")
    directory_name = conn.recv(directory_name_length).decode()
    print(directory_name)
    conn.sendall(b"1")
    try:
        os.mkdir(directory_name)
        conn.sendall(b"1")
    except OSError as error:
        print(error)
        conn.sendall(b"0")
    return None



while True:
    data = conn.recv(BUFFER_SIZE).decode()
    print(f"\nReceived: {format(data)}")
    if data == "LIST":
        list_files()
    elif data == "DELE":
        delete_file()
    elif data == "MKD":
        create_directory()
    elif data == "QUIT":
        break
    else:
        pass
    data = None




