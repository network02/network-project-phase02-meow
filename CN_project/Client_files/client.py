import socket
import os
import datetime



# Config
import struct
import sys

IP = "127.0.0.1"
PORT = 2001
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


def delete_file(file_name):
    print("Deleting file: {}...".format(file_name))
    try:
        socket.sendall(b"DELE")
        socket.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Encode the size of the file name
        format_string = "h"
        value = sys.getsizeof(file_name)
        packed_data = struct.pack(format_string, value)
        socket.sendall(packed_data)

        # Send the file name
        socket.sendall(file_name.encode())
    except:
        print("Couldn't send file details")
        return None
    try:
        file_exists = struct.unpack("i", socket.recv(4))[0]
        if file_exists == -1:
            print("The file does not exist on the server")
            return None
    except:
        print("Couldn't determine file existence")
        return None
    try:
        confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
        while confirm_delete != "Y" and confirm_delete != "N" and confirm_delete != "YES" and confirm_delete != "NO":
            print("Command not recognized, try again")
            confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
    except:
        print("Couldn't confirm deletion status")
        return None
    try:
        if confirm_delete == "Y" or confirm_delete == "YES":
            socket.sendall(b"Y")
            delete_status = struct.unpack("i", socket.recv(4))[0]
            if delete_status == 1:
                print("File successfully deleted")
                return None
            else:
                print("File failed to delete")
                return None
        else:
            socket.sendall(b"N")
            print("Delete abandoned by user!")
            return None
    except:
        print("Couldn't delete the file")
        return None


def create_directory(directory_name):
    # Delete specified file from the file server
    print("Creating Directory: {}...".format(directory_name))
    try:
        # Send request, then wait for go-ahead
        socket.sendall(b"MKD")
        socket.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        socket.sendall(struct.pack("h", sys.getsizeof(directory_name)))
        socket.recv(BUFFER_SIZE)
        socket.sendall(directory_name.encode())
        socket.recv(BUFFER_SIZE)
    except:
        print("Couldn't send Directory details")
        return None

    directory_check = int(socket.recv(BUFFER_SIZE).decode())
    if directory_check:
        print("directory created successfully.")
    else:
        print("couldn't create the directory.")
    return None


while True:
    # Listen for a command
    command = input("\nCommand -> ")

    if command.upper() == "CONN":
        connect()

    elif command.upper() == "LIST":
        list_of_files()

    elif command.upper() == "MKD":
        create_directory(input("Folder Name: "))

    elif command.upper() == "DELE":
        delete_file(input("\nFile name: "))

    elif command.upper() == "QUIT":
        break

    else:
        print("Enter a valid command!")