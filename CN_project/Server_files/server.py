import socket
import os

# Config
import struct
import sys
import time

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

def store_file_in_server():
    # Send message once server is ready to recieve file details
    conn.send(b'1')
    # Recieve file name length, then file name
    fileNameLength = struct.unpack(">h", conn.recv(2))[0]
    fileName = conn.recv(fileNameLength).decode('utf-8')
    # Send message to let client know server is ready for document content
    conn.send(b'1')
    # Recieve file size
    fileSize = struct.unpack(">i", conn.recv(4))[0]
    # Initialise and enter loop to recieve file content
    start_time = time.time()
    outputFile = open(fileName, 'wb')
    # This keeps track of how many bytes we have recieved, so we know when to stop the loop
    bytesReceived = 0
    print("\nReceiving...")
    while bytesReceived < fileSize:
        l = conn.recv(BUFFER_SIZE)
        outputFile.write(l)
        bytesReceived += BUFFER_SIZE
    outputFile.close()
    print("\nReceived file: {}".format(fileName))
    # Send upload performance details
    conn.send(struct.pack('>f', time.time() - start_time))
    conn.send(struct.pack('>i', fileSize))
    return

def download_file_from_server():
    # Send message indicating readiness to receive file details
    conn.send(b'1')

    # Receive file name length and extract it
    fileNameLength = struct.unpack(">h", conn.recv(2))[0]

    # Receive the entire file name from the client
    fileName = conn.recv(fileNameLength).decode('utf-8')

    # Check if the file exists on the server
    if os.path.isfile(fileName):
        # If the file exists, send its size to the client
        fileSize = struct.pack(">i", os.path.getsize(fileName))
        conn.send(fileSize)
    else:
        # If the file doesn't exist, send an error code to the client
        print("File name not valid")
        conn.sendall(struct.pack(">i", -1))
        return

    # Wait for client's acknowledgement to start sending the file
    conn.recv(BUFFER_SIZE)

    # Start the download timer
    start_time = time.time()
    print("Sending file...")

    # Open the file in binary read mode for reading
    content = open(fileName, 'rb')

    # Read the file in chunks of BUFFER_SIZE and send them to the client
    l = content.read(BUFFER_SIZE)
    while l:
        conn.send(l)
        l = content.read(BUFFER_SIZE)

    # Close the file handle
    content.close()

    # Receive the client's go-ahead before sending download details
    conn.recv(BUFFER_SIZE)

    # Send the download time to the client
    conn.sendall(struct.pack(">f", time.time() - start_time))
    return


while True:
    data = conn.recv(BUFFER_SIZE).decode()
    print(f"\nReceived: {format(data)}")
    if data == "LIST":
        list_files()
    if data == "STOR":
            store_file_in_server()
    if data == "RETR":
            download_file_from_server()
    if data == "QUIT":
        break
    else:
        pass
    data = None




