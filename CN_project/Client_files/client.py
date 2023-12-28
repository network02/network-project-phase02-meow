import socket
import os
import datetime



# Config
IP = "127.0.0.1"
PORT = 2000
BUFFER_SIZE = 1024
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect():
    # Connect to the server
    print("Sending request to server...")
    try:
        socket.connect((IP, PORT))
        print("Connected successfully!")
    except:
        print("Couldn't connect! :(")


def list_of_files():
    print("Requesting files...\n")
    try:
        socket.sendall(b"LIST")
    except:
        print("Couldn't make server request! check Connection.")
        return
    try:
        number_of_files = int.from_bytes(socket.recv(4), byteorder='big')
        for i in range(number_of_files):
            file_name_size = int.from_bytes(socket.recv(4), byteorder='big')
            file_name = socket.recv(file_name_size).decode()
            file_size = int.from_bytes(socket.recv(4), byteorder='big')
            file_creation_time_str = socket.recv(20).decode()
            file_creation_time = datetime.datetime.strptime(file_creation_time_str, '%Y-%m-%d %H:%M:%S')
            print("\t* {} | {}b | {}".format(file_name, file_size, file_creation_time.strftime('%Y-%m-%d %H:%M:%S')))
            socket.sendall(b"1")
    except:
        print("Couldn't retrieve listing")
        return
    try:
        socket.sendall(b"1")
        return
    except:
        print("Couldn't get final server confirmation")
        return


while True:
    # Listen for a command
    command = input("\nCommand -> ")
    if command.upper() == "CONN":
        connect()
    elif command.upper() == "LIST":
        list_of_files()
    elif command.upper() == "QUIT":
        break
    else:
        print("Enter a valid command!")