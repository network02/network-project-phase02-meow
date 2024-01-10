import socket as S
import os
import datetime
import struct
import sys
import time
from threading import Thread
from typing import Optional

users = [{'username': 'user1', 'password': '1234',
          'accessLevel': 'low'},

         {'username': 'user2', 'password': '1235',
          'accessLevel': 'low'},

         {'username': 'user3', 'password': '1236',
          'accessLevel': 'high'},

         {'username': 'admin', 'password': '0000',
          'accessLevel': 'full'}]

private_paths = [{'path': 'private1'},
                 {'path': 'private2'}]


class Client(Thread):
    IP = "127.0.0.1"
    PORT = 27
    BUFFER_SIZE = 1024

    def __init__(self, conn : S.socket) -> None:
        self.username_exist: bool = False
        self.conn: S.socket = conn
        self.authenticated: bool = False
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.current_directory: str = os.getcwd()
        # self.TCP_DATA_PORT = random.randint(4500, 4999)

        super().__init__()

    def run(self):
        while True:
            data = self.conn.recv(Client.BUFFER_SIZE).decode()
            print(f"\nReceived: {format(data)}")

            for i in range(len(users)):
                if data == users[i]["username"]:
                    self.username_exist = True
                    self.conn.send(b'1')
                    self.password = self.conn.recv(Client.BUFFER_SIZE).decode()
                    print(f"\nReceived: {format(self.password)}")
                    if self.password == users[i]["password"]:
                        self.conn.send(b'1')
                        self.authenticated = True
                    else:
                        self.conn.send(b'-1')
                        print("400 Invalid password")

            if not self.username_exist:
                self.conn.send(b'-1')
                print("400 Invalid username")
            if self.authenticated:
                if data == "LIST":
                    self.list_files()
                elif data == "STOR":
                    self.store_file_in_server()
                elif data == "RETR":
                    self.download_file_from_server()
                elif data == "DELE":
                    self.delete_file()
                elif data == "MKD":
                    self.create_directory()
                elif data == "RMD":
                    self.remove_directory()
                elif data == "PWD":
                    self.display_current_directory()
                elif data == "CWD":
                    self.change_directory()
                elif data == "CDUP":
                    self.change_directory_up()
                elif data == "QUIT":
                    self.conn.close()
                    break
                data = None

    def start_data_connection(self):
        # portRandom = random.randrange(3000, 50000)
        data_socket = S.socket(S.AF_INET, S.SOCK_STREAM)
        data_socket.bind(("127.0.0.1", 20))
        data_socket.listen()
        conn2, addr = data_socket.accept()
        return conn2

    def report(self):
        conn2 = self.start_data_connection()
        print("Reporting previous requests...\n")

        with open("report.txt", "r+") as report_file:
            # Reading form a file
            conn2.send(b'1')
            l = report_file.read(4096)
            conn2.send(l.encode('utf-8'))
        print("The report has been sent.\n")

    def list_files(self) -> None:
        conn2 = self.start_data_connection()
        print("Listing files...")
        listing = os.listdir(self.current_directory)
        conn2.send(len(listing).to_bytes(4, byteorder='big'))
        for i in listing:
            j = os.path.relpath(self.current_directory + '\\' + i, os.getcwd())
            conn2.send(len(i).to_bytes(4, byteorder='big'))
            conn2.send(i.encode())
            conn2.send(os.path.getsize(j).to_bytes(4, byteorder='big'))
            file_creation_time = os.path.getctime(j)
            file_creation_time_str = datetime.datetime.fromtimestamp(file_creation_time).strftime('%Y-%m-%d %H:%M:%S')
            conn2.send(file_creation_time_str.encode())
            self.conn.recv(Client.BUFFER_SIZE)
        print("Successfully sent file listing")
        return

    def store_file_in_server(self) -> None:
        conn2 = self.start_data_connection()
        # Send message once server is ready to recieve file details
        self.conn.send(b'1')
        # Recieve file name length, then file name
        fileNameLength = struct.unpack(">h", conn2.recv(2))[0]
        fileName = conn2.recv(fileNameLength).decode('utf-8')
        # Send message to let client know server is ready for document content
        self.conn.send(b'1')
        # Recieve file size
        fileSize = struct.unpack(">i", conn2.recv(4))[0]
        # Initialise and enter loop to recieve file content
        start_time = time.time()
        outputFile = open(self.current_directory + "\\" + fileName, 'wb')
        # This keeps track of how many bytes we have recieved, so we know when to stop the loop
        bytesReceived = 0
        print("\nReceiving...")
        while bytesReceived < fileSize:
            l = conn2.recv(Client.BUFFER_SIZE)
            outputFile.write(l)
            bytesReceived += Client.BUFFER_SIZE
        outputFile.close()
        print("\nReceived file: {}".format(fileName))
        # Send upload performance details
        conn2.send(struct.pack('>f', time.time() - start_time))
        conn2.send(struct.pack('>i', fileSize))
        return

    def download_file_from_server(self) -> None:
        conn2 = self.start_data_connection()
        # Send message indicating readiness to receive file details
        self.conn.send(b'1')

        # Receive file name length and extract it
        fileNameLength = struct.unpack(">h", conn2.recv(2))[0]

        # Receive the entire file name from the client
        fileName = conn2.recv(fileNameLength).decode('utf-8')

        if fileName.startswith("/"):
            directory, fileName = os.path.split(fileName)
            self.change_directory()
        if directory == private_paths[0]["path"]:
            # Check if the file exists on the server
            if os.path.isfile(self.current_directory + "\\" + fileName):
                # If the file exists, send its size to the client
                fileSize = struct.pack(">i", os.path.getsize(self.current_directory + "\\" + fileName))
                conn2.send(fileSize)
            else:
                # If the file doesn't exist, send an error code to the client
                print("File name not valid")
                self.conn.sendall(struct.pack(">i", -1))
                return

            # Wait for client's acknowledgement to start sending the file
            self.conn.recv(Client.BUFFER_SIZE)

            # Start the download timer
            start_time = time.time()
            print("Sending file...")

            # Open the file in binary read mode for reading
            content = open(fileName, 'rb')

            # Read the file in chunks of BUFFER_SIZE and send them to the client
            l = content.read(Client.BUFFER_SIZE)
            while l:
                print("server while")
                conn2.send(l)
                l = content.read(Client.BUFFER_SIZE)

            # Close the file handle
            self.conn.recv(Client.BUFFER_SIZE)

            content.close()

            # Receive the client's go-ahead before sending download details
            self.conn.recv(Client.BUFFER_SIZE)

            # Send the download time to the client
            # conn.sendall(struct.pack(">f", time.time() - start_time))
            print(f"{fileName} Successfully downloaded")

            return

    def delete_file(self) -> None:
        conn2 = self.start_data_connection()
        self.conn.sendall(b"1")
        file_name_length = struct.unpack("h", conn2.recv(2))[0]
        file_name = conn2.recv(file_name_length).decode()

        if os.path.isfile(self.current_directory + "\\" + file_name):
            self.conn.sendall(struct.pack("i", 1))
        else:
            self.conn.sendall(struct.pack("i", -1))
            return None
        confirm_delete = self.conn.recv(Client.BUFFER_SIZE).decode()
        if confirm_delete == "Y":
            try:
                os.remove(file_name)
                self.conn.sendall(struct.pack("i", 1))
            except:
                print("Failed to delete {}".format(file_name))
                self.conn.sendall(struct.pack("i", -1))
        else:
            print("Delete abandoned by the client!")
            return None

    def create_directory(self) -> None:
        conn2 = self.start_data_connection()
        # Send go-ahead
        self.conn.sendall(b"1")
        # Get Directory details
        directory_name_length = struct.unpack("h", conn2.recv(2))[0]
        print(directory_name_length)
        self.conn.sendall(b"1")
        directory_name = conn2.recv(directory_name_length).decode()
        print(directory_name)
        self.conn.sendall(b"1")
        try:
            os.mkdir(self.current_directory + "\\" + directory_name)
            self.conn.sendall(b"1")
        except OSError as error:
            print(error)
            self.conn.sendall(b"0")
        return None

    def remove_directory(self) -> None:
        conn2 = self.start_data_connection()
        # Send go-ahead
        self.conn.sendall(b"1")
        # Get Directory details
        directory_name_length = struct.unpack("h", conn2.recv(2))[0]
        directory_name = conn2.recv(directory_name_length).decode()
        print(directory_name)
        self.conn.sendall(b"1")
        try:
            if os.path.isabs(directory_name):
                os.rmdir(directory_name)
            else:
                os.rmdir(self.current_directory + "\\" + directory_name)
            # os.rmdir(directory_name)
            self.conn.sendall(b"1")
        except OSError as error:
            print(error)
            self.conn.sendall(b"0")
        return None

    def change_directory(self) -> None:
        # Send go-ahead
        # Get Directory details
        conn2 = self.start_data_connection()
        new_path_length = struct.unpack("h", conn2.recv(2))[0]
        new_path = conn2.recv(new_path_length).decode()
        try:
            if os.path.isabs(new_path):
                self.current_directory = new_path
            else:
                self.current_directory = self.current_directory + "\\" + new_path
            print(self.current_directory)
            # os.chdir(new_path)
            self.conn.sendall(b"1")
        except OSError as error:
            print(error)
            self.conn.sendall(b"0")
        return None

    def display_current_directory(self) -> None:
        try:
            conn2 = self.start_data_connection()
            # Send response to client
            self.conn.sendall(b'150 Opening data connection.')
            # cwd = os.getcwd()
            # print(cwd)
            # conn2.sendall(str(sys.getsizeof(cwd)).encode())
            # conn2.sendall(cwd.encode())
            print(self.current_directory)
            conn2.sendall(str(sys.getsizeof(self.current_directory)).encode())
            conn2.sendall(self.current_directory.encode())
            conn2.close()
            self.conn.sendall('226 Transfer complete.'.encode('utf-8'))
        except OSError as error:
            print(error)
        except Exception as e:
            print(e)
            print("couldn't send path.")
        return None

    def change_directory_up(self) -> None:
        try:
            print(self.current_directory)
            self.current_directory = os.path.dirname(self.current_directory)
            print(self.current_directory)
            # os.chdir('../')
            self.conn.sendall(b"1")
        except OSError as error:
            print(error)
            self.conn.sendall(b"0")
        return None


#
#
# IP = "127.0.0.1"
# PORT = 21
# BUFFER_SIZE = 1024
# socket = S.socket(S.AF_INET, S.SOCK_STREAM)
# socket.bind((IP, PORT))
# socket.listen(5)
#
# print(f"\nFTP server is online on {IP}:{PORT}!\n")
# conn, addr = socket.accept()
# # print("\nConnected to by address: {}".format(addr))
#
# username = conn.recv(BUFFER_SIZE).decode()
# print(f"\nReceived: {format(username)}")
#
# is_user_logged_in = False
# for i in range (len(users)):
#     if username == users[i]["username"]:
#         is_user_logged_in = True
#         conn.send(b'1')
#         password = conn.recv(BUFFER_SIZE).decode()
#         print(f"\nReceived: {format(password)}")
#         if password == users[i]["password"]:
#             conn.send(b'1')
#         else:
#             conn.send(b'-1')
#             print("400 Invalid password")
#
# if not is_user_logged_in:
#     conn.send(b'-1')
#     print("400 Invalid username")
#
#
# def start_data_connection():
#     # portRandom = random.randrange(3000, 50000)
#     data_socket = S.socket(S.AF_INET, S.SOCK_STREAM)
#     data_socket.bind(("127.0.0.1", 20))
#     data_socket.listen()
#     conn2, addr = data_socket.accept()
#     return conn2
#
#
# def list_files():
#     conn2 = start_data_connection()
#     print("Listing files...")
#     listing = os.listdir(os.getcwd())
#     conn2.send(len(listing).to_bytes(4, byteorder='big'))
#     for i in listing:
#         conn2.send(len(i).to_bytes(4, byteorder='big'))
#         conn2.send(i.encode())
#         conn2.send(os.path.getsize(i).to_bytes(4, byteorder='big'))
#         file_creation_time = os.path.getctime(i)
#         file_creation_time_str = datetime.datetime.fromtimestamp(file_creation_time).strftime('%Y-%m-%d %H:%M:%S')
#         conn2.send(file_creation_time_str.encode())
#         conn.recv(BUFFER_SIZE)
#     print("Successfully sent file listing")
#     return
#
#
# def store_file_in_server():
#     conn2 = start_data_connection()
#     # Send message once server is ready to recieve file details
#     conn.send(b'1')
#     # Recieve file name length, then file name
#     fileNameLength = struct.unpack(">h", conn2.recv(2))[0]
#     fileName = conn2.recv(fileNameLength).decode('utf-8')
#     # Send message to let client know server is ready for document content
#     conn.send(b'1')
#     # Recieve file size
#     fileSize = struct.unpack(">i", conn2.recv(4))[0]
#     # Initialise and enter loop to recieve file content
#     start_time = time.time()
#     outputFile = open(fileName, 'wb')
#     # This keeps track of how many bytes we have recieved, so we know when to stop the loop
#     bytesReceived = 0
#     print("\nReceiving...")
#     while bytesReceived < fileSize:
#         l = conn2.recv(BUFFER_SIZE)
#         outputFile.write(l)
#         bytesReceived += BUFFER_SIZE
#     outputFile.close()
#     print("\nReceived file: {}".format(fileName))
#     # Send upload performance details
#     conn2.send(struct.pack('>f', time.time() - start_time))
#     conn2.send(struct.pack('>i', fileSize))
#     return
#
#
# def download_file_from_server():
#     conn2 = start_data_connection()
#     # Send message indicating readiness to receive file details
#     conn.send(b'1')
#
#     # Receive file name length and extract it
#     fileNameLength = struct.unpack(">h", conn2.recv(2))[0]
#
#     # Receive the entire file name from the client
#     fileName = conn2.recv(fileNameLength).decode('utf-8')
#
#     # Check if the file exists on the server
#     if os.path.isfile(fileName):
#         # If the file exists, send its size to the client
#         fileSize = struct.pack(">i", os.path.getsize(fileName))
#         conn2.send(fileSize)
#     else:
#         # If the file doesn't exist, send an error code to the client
#         print("File name not valid")
#         conn.sendall(struct.pack(">i", -1))
#         return
#
#     # Wait for client's acknowledgement to start sending the file
#     conn.recv(BUFFER_SIZE)
#
#     # Start the download timer
#     start_time = time.time()
#     print("Sending file...")
#
#     # Open the file in binary read mode for reading
#     content = open(fileName, 'rb')
#
#     # Read the file in chunks of BUFFER_SIZE and send them to the client
#     l = content.read(BUFFER_SIZE)
#     while l:
#         print("server while")
#         conn2.send(l)
#         l = content.read(BUFFER_SIZE)
#
#     # Close the file handle
#     conn.recv(BUFFER_SIZE)
#
#     content.close()
#
#     # Receive the client's go-ahead before sending download details
#     conn.recv(BUFFER_SIZE)
#
#
#     # Send the download time to the client
#     # conn.sendall(struct.pack(">f", time.time() - start_time))
#     print(f"{fileName} Successfully downloaded")
#
#     return
#
#
#
# def delete_file():
#     conn2 = start_data_connection()
#     conn.sendall(b"1")
#     file_name_length = struct.unpack("h", conn2.recv(2))[0]
#     file_name = conn2.recv(file_name_length).decode()
#     if os.path.isfile(file_name):
#         conn.sendall(struct.pack("i", 1))
#     else:
#         conn.sendall(struct.pack("i", -1))
#         return None
#     confirm_delete = conn.recv(BUFFER_SIZE).decode()
#     if confirm_delete == "Y":
#         try:
#             os.remove(file_name)
#             conn.sendall(struct.pack("i", 1))
#         except:
#             print("Failed to delete {}".format(file_name))
#             conn.sendall(struct.pack("i", -1))
#     else:
#         print("Delete abandoned by the client!")
#         return None
#
#
# def create_directory():
#     conn2 = start_data_connection()
#     # Send go-ahead
#     conn.sendall(b"1")
#     # Get Directory details
#     directory_name_length = struct.unpack("h", conn2.recv(2))[0]
#     print(directory_name_length)
#     conn.sendall(b"1")
#     directory_name = conn2.recv(directory_name_length).decode()
#     print(directory_name)
#     conn.sendall(b"1")
#     try:
#         os.mkdir(directory_name)
#         conn.sendall(b"1")
#     except OSError as error:
#         print(error)
#         conn.sendall(b"0")
#     return None
#
#
# def remove_directory():
#     conn2 = start_data_connection()
#     # Send go-ahead
#     conn.sendall(b"1")
#     # Get Directory details
#     directory_name_length = struct.unpack("h", conn2.recv(2))[0]
#     directory_name = conn2.recv(directory_name_length).decode()
#     print(directory_name)
#     conn.sendall(b"1")
#     try:
#         os.rmdir(directory_name)
#         conn.sendall(b"1")
#     except OSError as error:
#         print(error)
#         conn.sendall(b"0")
#     return None
#
#
# def change_directory():
#     # Send go-ahead
#     # Get Directory details
#     conn2 = start_data_connection()
#     new_path_length = struct.unpack("h", conn2.recv(2))[0]
#     new_path = conn2.recv(new_path_length).decode()
#     try:
#         os.chdir(new_path)
#         conn.sendall(b"1")
#     except OSError as error:
#         print(error)
#         conn.sendall(b"0")
#     return None
#
#
# def display_current_directory():
#     try:
#         conn2 = start_data_connection()
#         # Send response to client
#         conn.sendall(b'150 Opening data connection.')
#         cwd = os.getcwd()
#         print(cwd)
#         conn2.sendall(str(sys.getsizeof(cwd)).encode())
#         conn2.sendall(cwd.encode())
#
#         conn2.close()
#         conn.sendall('226 Transfer complete.'.encode('utf-8'))
#     except OSError as error:
#         print(error)
#     except Exception as e:
#         print(e)
#         print("couldn't send path.")
#     return None
#
#
# def change_directory_up():
#     try:
#         os.chdir('../')
#         conn.sendall(b"1")
#     except OSError as error:
#         print(error)
#         conn.sendall(b"0")
#     return None
#
#
#
# while True:
#
#     data = conn.recv(BUFFER_SIZE).decode()
#     print(f"\nReceived: {format(data)}")
#     if data == "LIST":
#         list_files()
#     if data == "STOR":
#         store_file_in_server()
#     if data == "RETR":
#         download_file_from_server()
#     if data == "DELE":
#         delete_file()
#     if data == "MKD":
#         create_directory()
#     if data == "RMD":
#         remove_directory()
#     if data == "PWD":
#         display_current_directory()
#     if data == "CWD":
#         change_directory()
#     if data == "CDUP":
#         change_directory_up()
#     if data == "PASV":
#         data_socket = start_data_connection()
#     if data == "QUIT":
#         pass
#     data = None


if __name__ == "__main__":
        print("Welcome to the FTP server.\nTo get started, connect a client.")

        with S.socket(S.AF_INET, S.SOCK_STREAM) as socket1:
            socket1.bind((Client.IP, Client.PORT))
            socket1.listen(10)

            while True:
                client_socket, client_address = socket1.accept()
                print(f"\nConnected to by address: {client_address}")
                new_client = Client(client_socket)
                new_client.start()


