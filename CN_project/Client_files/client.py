import socket


# Config
IP = "127.0.0.1"
PORT = 6156
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

while True:
    # Listen for a command
    command = input("\nCommand -> ")
    if command.upper() == "CONN":
        connect()
    elif command.upper() == "QUIT":
        break
    else:
        print("Enter a valid command!")