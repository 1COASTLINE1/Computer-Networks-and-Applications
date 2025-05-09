from socket import *
import sys
import re
import os

#Server would be running on the same host as Client
if len(sys.argv) != 2:
    print("\n===== Error usage, python3 Clinet.py SERVER_PORT ======\n")
    exit(0)

serverPort = int(sys.argv[1])
serverHost = "127.0.0.1"
serverAddress = (serverHost, serverPort)

# Create UDP socket
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1.0) 
print("\n===== Client is running =====")
print("Start by typing your username or create a new one")


#Deal with loss packets
def handle_timeout(socket,message,address,timeout_time=1):

    for chance in range(1, 3):
        try:
            socket.settimeout(timeout_time)
            socket.sendto(message.encode(), address)
            response, serverAddress = socket.recvfrom(2048)
            return response.decode()
        except socket.timeout:
            print("The server is not responding. There may be a pocket loss issue.")
            print("Please make sure the server is running and try again.")
            if chance == 2:
                print("The server is not responding. Retries run out.")
                return None

#Deal with login and registration
while True:
    Username = input("Please enter your Username: ")
    matched_string = r'^[a-zA-Z0-9~!@#$%^&*_\-+=`|\\()\[\]{}:;\"\'<>,.?/]+$'

    if not re.match(matched_string, Username):
        print("Invalid username. Please use allowed pattern:a-zA-Z0-9~!@#$%^&*_-+=`|\\(){}\[\]:\"\'<>,.?/")
        continue

    # send username to server
    response = handle_timeout(clientSocket, Username, serverAddress)

    if response is None:
        continue 


    if 'enter' in response:
        if 'New user' not in response:
            # Existing user login process
            while True:
                password = input("Please enter your password: ")
                if not re.fullmatch(matched_string, password):
                    print("Invalid password. Please use allowed characters.")
                    continue

                response = handle_timeout(clientSocket, password, serverAddress)
                if not response:
                    continue
                print(f'{response}')

                if 'successful' in response:
                    break  

            break 

        else:
            # New user registration
            while True:
                password = input("Please set your password: ")
                if not re.fullmatch(matched_string, password):
                    print("Invalid password. Please use allowed characters.")
                    continue

                response = handle_timeout(clientSocket, password, serverAddress)
                if not response:
                    continue

                print(response)
                if 'successful' in response:
                    break  

            break 


    elif 'already logged in' in response or 'try again' in response:
        print(f'{response}')

print("You are now logged in! Ready to continue...\n")
print("Please enter the following commands: CRT <threadtitle>, MSG <threadtitle> <message>, LST, RDT <threadtitle>, DLT <threadtitle> <message number>, EDT <threadtitle> <message number> <new message>, RMV <threadtitle>, XIT, UPD <threadtitle> <filename>, DWN <threadtitle> <filename>\n")



    

#Deal with thread commands
while True:
    command = input("Please enter the command: ").strip()
    tokens = command.split()

    if tokens == []:
        print("Empty command.")
        continue

    if tokens[0].upper() not in ['CRT','MSG','DLT', 'EDT', 'LST', 'RDT',  'RMV', 'XIT','UPD',"DWN"]:
        print("Invalid command. Please use: CRT, MSG, DLT, EDT, LST, RDT, RMV, XIT, UPD, DWN") 
 

    # Check if the command is capitalized
    if tokens[0]!= tokens[0].upper():
        print("Command should be in uppercase.")
        continue

    elif tokens[0] == 'CRT':
        if len(tokens) != 2:
            print("Invalid command. Usage: CRT <threadtitle>")
            continue
        else:
            response = handle_timeout(clientSocket, command, serverAddress)
            if response:
                print(f"{response}")

            if 'already exists' in response:
                continue
     
    elif tokens[0] == 'MSG':
        if len(tokens) < 3:
            print("Invalid command. Please use MSG <threadtitle> <message>")
            continue
        else:
            response = handle_timeout(clientSocket, command, serverAddress)
            if response:
                print(f"{response}")

    elif tokens[0] == 'DLT':
        if len(tokens) != 3:
            print("Invalid command. Usage: DLT <threadtitle> <message number>")
            continue
        elif not tokens[2].isdigit() or int(tokens[2]) <= 0:
            print("Invalid message number. Please enter a positive integer.")
            continue
        else:
            response = handle_timeout(clientSocket, command, serverAddress)
            if response:
                print(f"{response}")
    
    elif tokens[0] == 'EDT':
        if len(tokens) < 4:
            print("Invalid command. Please use EDT <threadtitle> <message number> <new message>")
            continue
        elif not tokens[2].isdigit() or int(tokens[2]) <= 0:
            print("Invalid message number. Please enter a positive integer.")
            continue
        else:
            response = handle_timeout(clientSocket, command, serverAddress)
            if response:
                print(f"{response}")
    
    elif tokens[0] == 'LST':
        if len(tokens) != 1:
            print("Invalid command.Please use: LST")
            continue
        else:
           response = handle_timeout(clientSocket, command, serverAddress)
           if response:
                 print(f"{response}\n")


    elif tokens[0] == 'RDT':
        if len(tokens) != 2:
            print("Invalid command. Please use  RDT <threadtitle>")
            continue
        else:
            response = handle_timeout(clientSocket, command, serverAddress)
            if response:
                print(f"{response}")
    
    elif tokens[0] == "RMV":
        if len(tokens) != 2:
            print("Invalid command. Please use RMV <threadtitle>")
            continue
        else:
            response = handle_timeout(clientSocket, command, serverAddress)
            if response:
                print(f"{response}")
    
    elif tokens[0] == "XIT":
        if len(tokens) != 1:
            print("Invalid command. If you want to exit, please use: XIT")
            continue
        else:
            response = handle_timeout(clientSocket, command, serverAddress)
            if response:
                print(f"{response}")
                break

    elif tokens[0] == 'UPD':
        if len(tokens) != 3:
            print("Invalid command. Please use UPD <threadtitle> <filename>")
            continue
        else:
            thread_title = tokens[1]
            file_name = tokens[2]

            if not os.path.isfile(file_name):
                print(f"File {file_name} does not exist.")
                continue

            satisfied_pattern = r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)?$'
            if not re.match(satisfied_pattern, thread_title):
                print("Invalid thread title. Please use allowed pattern: a-zA-Z0-9")
                continue

            response = handle_timeout(clientSocket, command, serverAddress)
            if not response:
                print("No response from server.")
                continue
            
            print(f"{response}")

            if "ready for" in response:
                try:
                    tcp_socket = socket(AF_INET, SOCK_STREAM)
                    tcp_socket.connect(serverAddress)
                    print(f"Connected to server for file upload.")
                    with open(file_name, "rb") as file:
                        data = file.read(2048)
                        if not data:
                            print("File is empty.")

                        tcp_socket.sendall(data)
                    tcp_socket.close()
                    print(f"File {file_name} uploaded successfully.")
                    print("Connection closed.")

                    finalresponse, serverAddress = clientSocket.recvfrom(2048)
                    print(f"{finalresponse.decode()}")

                except Exception as e:
                    print(f"Error uploading file: {e}")
                    continue

    elif tokens[0] == 'DWN':
        if len(tokens) != 3:
            print("Invalid command. Please use DWN <threadtitle> <filename>")
            continue
        else:
            thread_title = tokens[1]
            file_name = tokens[2]

            satisfied_pattern = r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)?$'
            if not re.match(satisfied_pattern, thread_title):
                print("Invalid thread title. Please use allowed pattern: a-zA-Z0-9")
                continue

            response = handle_timeout(clientSocket, command, serverAddress)
            if not response:
                print("No response from server.")
                continue
            
            print(f"{response}")

            if "ready for" in response:
                try:
                    tcp_socket = socket(AF_INET, SOCK_STREAM)
                    tcp_socket.connect(serverAddress)
                    print(f"Connected to server for file download.")

                    with open(file_name, "wb") as file:
                        while True:
                            data = tcp_socket.recv(2048)
                            if data == b"":
                                break
                            file.write(data)

                    tcp_socket.close()
                    print(f"File {file_name} downloaded successfully.")
                    print("Connection closed.")

                except Exception as e:
                    print(f"Error downloading file: {e}")
                    continue
# close the socket
clientSocket.close()
