import socket as S
import os
import datetime
import struct
import sys
import threading
import time

# Config
import struct
import sys

IP = "127.0.0.1"
PORT = 21
BUFFER_SIZE = 1024
socket = S.socket(S.AF_INET, S.SOCK_STREAM)

def connect(username, password):
    # Connect to the server
    print("Sending request to server...")
    try:
        socket.connect((IP, PORT))
        print("200 Socket connected successfully!")
        socket.send(username.encode('utf-8'))
        ack = socket.recv(BUFFER_SIZE)
        if ack == b'1':
            socket.send(password.encode('utf-8'))
            ack = socket.recv(BUFFER_SIZE)
            if ack == b'1':
                print("200 You are logged in!")
            else:
                print("400 The password you entered is not valid.")
        else:
            print("400 The username you entered is not valid.")
    except:
        print("Couldn't connect! :(")


def start_data_connection():
    data_socket = S.socket(S.AF_INET, S.SOCK_STREAM)
    data_socket.connect(("127.0.0.1", 20))
    return data_socket


def list_of_files():
    print("Requesting files...\n")
    try:
        socket.sendall(b"LIST")
        data_socket = start_data_connection()
    except:
        print("Couldn't make server request! check Connection.")
        return
    try:
        number_of_files = int.from_bytes(data_socket.recv(4), byteorder='big')
        for i in range(number_of_files):
            file_name_size = int.from_bytes(data_socket.recv(4), byteorder='big')
            file_name = data_socket.recv(file_name_size).decode()
            file_size = int.from_bytes(data_socket.recv(4), byteorder='big')
            file_creation_time_str = data_socket.recv(20).decode()
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


def upload_file_on_server(fileName):
    # Upload a file
    print("\nUploading file: {}...".format(fileName))
    try:
        # Check the file exists
        content = open(fileName, 'rb')
    except:
        print("Couldn't open file. Make sure the file name was entered correctly.")
        return
    try:
        # Make upload request
        socket.send(b'STOR')
        data_socket = start_data_connection()
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return
    try:
        # Wait for server acknowledgement then send file details
        # Wait for server ok
        socket.recv(BUFFER_SIZE)
        # Send file name size and file name
        fileNameSize = struct.pack(">h", sys.getsizeof(fileName))
        data_socket.send(fileNameSize)
        data_socket.send(fileName.encode('utf-8'))
        # Wait for server ok then send file size
        socket.recv(BUFFER_SIZE)
        filePath = os.path.realpath(fileName)
        fileSize = struct.pack(">i", os.path.getsize(filePath))
        data_socket.send(fileSize)
    except:
        print("Error sending file details")
    try:
        # Send the file in chunks defined by BUFFER_SIZE
        # Doing it this way allows for unlimited potential file sizes to be sent
        l = content.read(BUFFER_SIZE)
        print("\nSending...")
        while l:
            data_socket.send(l)
            l = content.read(BUFFER_SIZE)
        content.close()
        # Get upload performance details
        uploadTime = struct.unpack(">f", data_socket.recv(4))[0]
        uploadSize = struct.unpack(">i", data_socket.recv(4))[0]
        print("\nSent file: {}\nTime elapsed: {:.2f}s\nFile size: {:,}b".format(fileName, uploadTime, uploadSize))
    except:
        print("Error sending file")
        return
    return


def download_file_from_server(fileName):
    # Download the specified file
    print("Downloading file: {}".format(fileName))
    try:
        # Send download request to the server
        socket.send(b'RETR')
        data_socket = start_data_connection()
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return
    try:
        # Wait for server's acknowledgement and check file existence
        socket.recv(BUFFER_SIZE)

        # Send file name length and file name to the server
        fileNameSize = struct.pack(">h", sys.getsizeof(fileName))
        data_socket.send(fileNameSize)
        data_socket.send(fileName.encode('utf-8'))

        # Receive file size from the server
        fileSize = struct.unpack(">i", data_socket.recv(4))[0]
        if fileSize == -1:
            # If file size is -1, file doesn't exist
            print("File does not exist. Make sure the name was entered correctly")
            return
    except:
        print("Error checking file")
    try:
        # Send acknowledgement to proceed with file transfer
        socket.send(b'1')

        # Start the download timer
        start_time = time.time()

        # Open the file for writing in binary mode
        outputFile = open(fileName, 'wb')

        # Download the file in chunks of BUFFER_SIZE
        bytesReceived = 0
        print("\nDownloading...")
        while bytesReceived < fileSize:
            l = data_socket.recv(BUFFER_SIZE)
            outputFile.write(l)
            bytesReceived += BUFFER_SIZE
            print("while")

        # Close the file handler
        socket.sendall(b"1")

        outputFile.close()

        # Send acknowledgement to receive download details
        socket.send(b'1')

        # Receive download performance details
        # downloadTime = struct.unpack(">f", socket.recv(4))[0]
        # downloadSize = struct.unpack(">i", socket.recv(4))[0]
        print(f"{fileName} Successfully downloaded")
    except:
        print("Error downloading file")
        return
    return



def delete_file(file_name):
    print("Deleting file: {}...".format(file_name))
    try:
        socket.sendall(b"DELE")
        data_socket = start_data_connection()
        socket.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Encode the size of the file name
        format_string = "h"
        value = sys.getsizeof(file_name)
        packed_data = struct.pack(format_string, value)
        data_socket.sendall(packed_data)

        # Send the file name
        data_socket.sendall(file_name.encode())
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
        data_socket = start_data_connection()
        socket.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        data_socket.sendall(struct.pack("h", sys.getsizeof(directory_name)))
        socket.recv(BUFFER_SIZE)
        data_socket.sendall(directory_name.encode())
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


def remove_directory(directory_name):
    print("Removing Directory: {}...".format(directory_name))
    try:
        socket.sendall(b"RMD")
        data_socket = start_data_connection()
        socket.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        data_socket.sendall(struct.pack("h", sys.getsizeof(directory_name)))
        data_socket.sendall(directory_name.encode())
        socket.recv(BUFFER_SIZE)
    except:
        print("Couldn't send Directory details")
        return None

    directory_check = int(socket.recv(BUFFER_SIZE).decode())
    if directory_check:
        print("directory removed successfully.")
    else:
        print("couldn't remove the directory.")
    return None


def change_directory(new_path):
    print("Changing Directory: {}...".format(new_path))
    try:
        # Send request, then wait for go-ahead
        socket.sendall(b"CWD")
        data_socket = start_data_connection()
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        data_socket.sendall(struct.pack("h", sys.getsizeof(new_path)))
        data_socket.sendall(new_path.encode())
    except:
        print("Couldn't send Path details")
        return None

    change_check = int(socket.recv(BUFFER_SIZE).decode())
    if change_check:
        print("path changed successfully.")
    else:
        print("couldn't change path.")
    return None


def display_current_directory():
    try:
        # Send request, then wait for go-ahead
        # data_socket_client = send_pasv_command(socket)
        socket.sendall(b"PWD")
        data_socket = start_data_connection()
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        path_len = int(data_socket.recv(BUFFER_SIZE).decode())
        path = data_socket.recv(path_len).decode()
        print(path)
    except:
        print("Couldn't receive path.")
        return None
    return None


def change_directory_up():
    try:
        socket.sendall(b"CDUP")
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None

    change_check = int(socket.recv(BUFFER_SIZE).decode())
    if change_check:
        print("path changed successfully.")
        display_current_directory()
    else:
        print("couldn't change path.")
    return None


while True:
    # Listen for a command
    command = input("\nCommand -> ").split()

    if command[0].upper() == "CONN":
        username = input("Username: ")
        password = input("Password: ")
        connect(username, password)


    elif command[0].upper() == "LIST":
        list_of_files()

    elif command[0].upper() == "STOR":
        upload_file_on_server(input("File name: "))

    elif command[0].upper() == "RETR":
        download_file_from_server(input("File name: "))

    elif command[0].upper() == "MKD":
        create_directory(input("Folder name: "))

    elif command[0].upper() == "DELE":
        delete_file(input("File name: "))

    elif command[0].upper() == "RMD":
        remove_directory(command[1])

    elif command[0].upper() == "PWD":
        display_current_directory()

    elif command[0].upper() == "CWD":
        change_directory(command[1])

    elif command[0].upper() == "CDUP":
        change_directory_up()

    elif command[0].upper() == "QUIT":
        break

    else:
        print("Enter a valid command!")
