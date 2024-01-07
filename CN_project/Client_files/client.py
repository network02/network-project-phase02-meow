import socket
import os
import datetime
import struct
import sys
import time

# Config
IP = "127.0.0.1"
PORT = 2000
BUFFER_SIZE = 1024
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

def authorization(username, password):
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
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return
    try:
        # Wait for server acknowledgement then send file details
        # Wait for server ok
        socket.recv(BUFFER_SIZE)
        # Send file name size and file name
        fileNameSize = struct.pack(">h", sys.getsizeof(fileName))
        socket.send(fileNameSize)
        socket.send(fileName.encode('utf-8'))
        # Wait for server ok then send file size
        socket.recv(BUFFER_SIZE)
        filePath = os.path.realpath(fileName)
        fileSize = struct.pack(">i", os.path.getsize(filePath))
        socket.send(fileSize)
    except:
        print("Error sending file details")
    try:
        # Send the file in chunks defined by BUFFER_SIZE
        # Doing it this way allows for unlimited potential file sizes to be sent
        l = content.read(BUFFER_SIZE)
        print("\nSending...")
        while l:
            socket.send(l)
            l = content.read(BUFFER_SIZE)
        content.close()
        # Get upload performance details
        uploadTime = struct.unpack(">f", socket.recv(4))[0]
        uploadSize = struct.unpack(">i", socket.recv(4))[0]
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
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return
    try:
        # Wait for server's acknowledgement and check file existence
        socket.recv(BUFFER_SIZE)

        # Send file name length and file name to the server
        fileNameSize = struct.pack(">h", sys.getsizeof(fileName))
        socket.send(fileNameSize)
        socket.send(fileName.encode('utf-8'))

        # Receive file size from the server
        fileSize = struct.unpack(">i", socket.recv(4))[0]
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
            l = socket.recv(BUFFER_SIZE)
            outputFile.write(l)
            bytesReceived += BUFFER_SIZE

        # Close the file handler
        outputFile.close()

        # Send acknowledgement to receive download details
        socket.send(b'1')

        # Receive download performance details
        downloadTime = struct.unpack(">f", socket.recv(4))[0]
        downloadSize = struct.unpack(">i", socket.recv(4))[0]
        print("Successfully downloaded {}.\nTime elapsed: {:.2f}s\nFile size: {:,}b".format(fileName, downloadTime,
                                                                                            downloadSize))
    except:
        print("Error downloading file")
        return
    return


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
    elif command.upper() == "STOR":
        fileName = input("file name: ")
        upload_file_on_server(fileName)
    elif command.upper() == "RETR":
        fileName = input("file name: ")
        download_file_from_server(fileName)
    elif command.upper() == "QUIT":
        break
    else:
        print("Enter a valid command!")
