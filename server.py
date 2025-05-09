from socket import *
import sys
import select
import threading
import os


# === Global thread locks ===
Concurrency_control_locks = {}  
Concurrency_control_locks_lock = threading.Lock()  

# Parse command line arguments 
if len(sys.argv) != 2:
    print("\n===== Error usage, python3 Server.py SERVER_PORT ======\n")
    exit(0)

serverPort = int(sys.argv[1])
serverHost = "127.0.0.1"
serverAddress = (serverHost, serverPort)

# Create sockets 
# UDP socket for commands
udp_Socket = socket(AF_INET, SOCK_DGRAM)
udp_Socket.bind(serverAddress)

# TCP socket for file transfers
tcp_Socket = socket(AF_INET, SOCK_STREAM)
tcp_Socket.bind(serverAddress)
tcp_Socket.listen(5)

print("\n===== Server is running =====")
print("===== Waiting for client messages or file transfer requests...=====")


active_users = {}
client_states = {}
file_user_container = {}


#Handle credentials file
def handle_credentials_file():
    """
    Load user credentials from the specified file.
    """
    container = {}
    #read the credentials.txt file and store the username and password in a dictionary
    with open("credentials.txt", "r") as file:
        for line in file:
            username, password = line.strip().split()
            container[username] = password
    
    return container

#add a new user to the credentials file
def append_credentials_file(username, password):
    """
    Append new user credentials to the credentials file.
    """
    with open("credentials.txt", "a") as file:
        file.write(f"{username} {password}\n")

#Handle create thread command
def handle_create_thread_command(username, thread_name):
    """
    Handle the command to create a new thread.
    """
    print(f"[{username}] Try to Create thread: {thread_name}")
    with Concurrency_control_locks_lock:
        if thread_name not in Concurrency_control_locks:
            Concurrency_control_locks[thread_name] = threading.Lock()
    with Concurrency_control_locks[thread_name]:
        if os.path.exists(thread_name):
            print(f"[{username}]'s Thread {thread_name} already exists.")
            return f"Thread {thread_name} already exists."
        else:
            with open(thread_name, "w") as f:
                f.write(f"{username}\n")
            print (f"[{username}] Create thread: {thread_name} successfully")
            return f"Thread {thread_name} created successfully."

#Check if thread exists, message number is valid, and user owns the message.
def validate_message_owner_and_format(username, thread_name, message_number):
    """
    Check if thread exists, message number is valid, and user owns the message.
    """
    if not os.path.exists(thread_name):
        print (f"[{username}]'s Thread {thread_name} does not exist.")
        return f"Thread {thread_name} does not exist.", False

    with open(thread_name, "r") as f:
        total_lines = f.readlines()


    current_num = 1
    for index in range(1, len(total_lines)):  # Skip creator line
        line = total_lines[index].strip()
        if line[0].isdigit():
            if current_num == message_number:
                parts = line.split()
                true_username = parts[1].rstrip(':')
                if true_username != username:
                    print (f"[{username}] trying to edit/delete someone else's message. Request denied.")
                    return f"You are trying to edit/delete someone else's message. Please check the message number.", False
                return total_lines, True
            current_num += 1

    print(f"[{username}] Message number {message_number} does not exist in thread {thread_name}.")
    return f"Message number {message_number} does not exist in thread {thread_name}.", False

#Handle post message command
def handle_post_message_command(username, thread_name, message):
    """
    Handle the command to post a message to a thread.
    """
    print(f"[{username}] Try to Post message: {message} to thread: {thread_name}")
    with Concurrency_control_locks_lock:
        if thread_name not in Concurrency_control_locks:
            Concurrency_control_locks[thread_name] = threading.Lock()
    with Concurrency_control_locks[thread_name]:
        if not os.path.exists(thread_name):
            print (f"[{username}]'s Thread {thread_name} does not exist.")
            return f"Thread {thread_name} does not exist."
        
        max_number = 0
        with open(thread_name, "r") as f:
                for i in f:
                    parts = i.strip().split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        max_number = max(max_number, int(parts[0]))

        number = max_number + 1
        input_message = f"{number} {username}: {message}\n"

        with open(thread_name, "a") as f:
            f.write(input_message)
        
        print(f"[{username}] Post message: {input_message.strip()} to thread: {thread_name} successfully")
        response = f"Message posted to thread {thread_name} successfully."

        return response
            
#Handle delete comment in thread command
def handle_delete_message_command(username, thread_name, message_number):
    """
    Handle the command to delete a message from a thread.
    """
    print(f"[{username}] Try to Delete message: {message_number} from thread: {thread_name}")
    message_number = int(message_number)
    with Concurrency_control_locks_lock:
        if thread_name not in Concurrency_control_locks:
            Concurrency_control_locks[thread_name] = threading.Lock()
    with Concurrency_control_locks[thread_name]:
        result, Truth_value = validate_message_owner_and_format(username, thread_name, message_number)
        if not Truth_value:
            return result
        
        total_lines = result
        # Delete the message and renumber the other messages
        new_lines = [total_lines[0]]  # Preserve the first line (thread owner)

        current_number = 1
        real_msg_num = 1
        for i in range(1, len(total_lines)):
            line = total_lines[i].strip()
            if line[0].isdigit():
                if current_number == message_number:
                    current_number += 1
                    continue 
                line_parts = line.split(maxsplit=2)
                if len(line_parts) >= 3:
                    user_name = line_parts[1]
                    content = line_parts[2]
                    new_lines.append(f"{real_msg_num} {user_name} {content}\n")
                    real_msg_num += 1
                current_number += 1
            else:
                new_lines.append(total_lines[i])

        with open(thread_name, "w") as f:
            f.writelines(new_lines)

        print(f"[{username}] Delete the {message_number}'s message in thread: {thread_name} successfully")
        return f"Message number {message_number} deleted from thread {thread_name} successfully."

#Handle edit thread command
def handle_edit_thread_command(username, thread_name, message_number, new_message):
    """
    Handle the command to edit a message in a thread.
    """
    print(f"[{username}] Try to Edit message: {message_number} in thread: {thread_name}")
    message_number = int(message_number)

    with Concurrency_control_locks_lock:
        if thread_name not in Concurrency_control_locks:
            Concurrency_control_locks[thread_name] = threading.Lock()

    with Concurrency_control_locks[thread_name]:
        result, Truth_value = validate_message_owner_and_format(username, thread_name, message_number)
        if not Truth_value:
            return result
        
        total_lines = result
        
        # Edit the message
        target_idex = -1
        current_num = 1
        for i in range(1, len(total_lines)):  # Skip the first line (creator info)
            line = total_lines[i].strip()
            if line[0].isdigit():
                if current_num == message_number:
                    target_idex = i
                    break
                current_num += 1
        if target_idex == -1:
            return f"Message number {message_number} not found."
        
        target_line = total_lines[target_idex].strip().split(maxsplit=2)
        msg_num = target_line[0]
        original_username = target_line[1]
        total_lines[target_idex] = f"{msg_num} {original_username} {new_message}\n"

        #Write the changes back to the file
        with open(thread_name, "w") as f:
            f.writelines(total_lines)

        print(f"[{username}] Edited message {message_number} in thread: {thread_name} successfully")
        return f"Message number {message_number} edited in thread {thread_name} successfully."

#Handle list thread command
def handle_list_thread_command(username):
    """
    Handle the command to list messages in a thread.
    """
    print(f"[{username}] Try to List all threads")
    threads = []
    for file_name in os.listdir("."):
        if os.path.isfile(file_name) and not file_name.endswith(".py") and file_name != "credentials.txt":
            threads.append(file_name)
    
    if threads == []:
        print(f"[{username}] request to list threads, but no threads avaislable.")
        return "No threads available."

    #Display the list of threads to the user
    print(f"[{username}] request to list threads, available threads: {threads}")
    thread = ""
    for line in threads:
        thread += line.strip() + "\n"
    return "Available threads:\n" + thread.rstrip()
                
#Handle read thread command
def handle_read_thread_command(username, thread_name):
    """
    Handle the command to read messages in a thread.
    """
    print(f"[{username}] Try to Read thread: {thread_name}")
    with Concurrency_control_locks_lock:
        if thread_name not in Concurrency_control_locks:
            Concurrency_control_locks[thread_name] = threading.Lock()
    with Concurrency_control_locks[thread_name]:
        if not os.path.exists(thread_name):
            print(f"[{username}] request to read thread: {thread_name}, but it does not exist.")
            return f"Thread {thread_name} does not exist."
        
        with open(thread_name, "r") as f:
            total_lines = f.readlines()
        
        #ignore the first line (thread owner)
        total_lines = total_lines[1:]

        if total_lines is None:
            print(f"[{username}] request to read thread: {thread_name}, but it is empty.")
            return f"Thread {thread_name} is empty."
        
        # Display the messages to the user
        print(f"[{username}] request to read thread: {thread_name} successfully")
        msg_per_line =''
        for line in total_lines:
            msg_per_line += line.strip() + "\n"
        return f"Messages in thread {thread_name}:\n" + msg_per_line.rstrip()

#Handle delete thread command
def handle_delete_thread_command(username, thread_name):
    """
    Handle the command to delete a thread.
    """
    print(f"[{username}] Try to Delete thread: {thread_name}")
    with Concurrency_control_locks_lock:
        if thread_name not in Concurrency_control_locks:
            Concurrency_control_locks[thread_name] = threading.Lock()
    with Concurrency_control_locks[thread_name]:
        if not os.path.exists(thread_name):
            print(f"[{username}] try to delete thread: {thread_name}, but it does not exist.")
            return f"Thread {thread_name} does not exist."
        
        owner_of_thread = ""
        with open(thread_name, "r") as f:
            total_lines = f.readlines()
            owner_of_thread = total_lines[0].strip()

        if owner_of_thread != username:
            print(f"[{username}] try to delete thread: {thread_name}, but the current user is not the creater.")
            return f"You are not the creater of thread {thread_name}. Deletion denied."
        
        os.remove(thread_name)

        for file_name in os.listdir("."):
            if file_name.startswith(thread_name + "-"):
                os.remove(file_name)
        
        print(f"[{username}] Delete thread: {thread_name} successfully")
        return f"Thread {thread_name} has been deleted successfully."

#Handle Exit command
def handle_exit_command(username,clientAddress):
    """
    Handle the command to exit the server.
    """
    print(f"[{username}] try to Exit the server.")
    active_users.pop(clientAddress)
    print(f"[{username}] exits the server successfully.")
    return "You have exited the server successfully.See you next time!"

#Handle TCP file transfer
def handle_tcp_file_transfer(socket_receive, addr):
    """
    Handle a single TCP file transfer session.
    """
    print(f"TCP connection established with {addr}.")
    IP = addr[0]
    file_info = file_user_container.get(IP)
    if file_info is None:
        print(f"Unexpected TCP connection from {addr}")
        socket_receive.close()
        return

    username = file_info["username"]
    thread_name = file_info["thread_name"] 
    file_name = file_info["file_name"]
    type = file_info["type"]
    final_file_name = f"{thread_name}-{file_name}"
    
    try:
        if type == "upload":
            print(f"[{username}] start uploading file: {file_name} to thread: {thread_name}")
            with Concurrency_control_locks_lock:
                if thread_name not in Concurrency_control_locks:
                    Concurrency_control_locks[thread_name] = threading.Lock()

            with Concurrency_control_locks[thread_name]:
                with open(final_file_name, "wb") as f:
                    while True:
                        data = socket_receive.recv(2048)
                        if not data:
                            break
                        f.write(data)
                
                #Write the file information to the thread file
                with open(thread_name, "a") as thread_file:
                    thread_file.write(f"{username} uploaded {file_name}\n")

            udp_addr = file_info.get("udp_address")
            udp_Socket.sendto(f"You have uploaded file {file_name} successfully.".encode(), udp_addr)
            print(f"[{username}] uploaded file {file_name} to thread {thread_name} successfully.")

        elif type == "download":
            print(f"[{username}] start downloading file: {file_name} from thread: {thread_name}")
            with Concurrency_control_locks_lock:
                if thread_name not in Concurrency_control_locks:
                    Concurrency_control_locks[thread_name] = threading.Lock()

            with Concurrency_control_locks[thread_name]:
                with open(final_file_name, "rb") as f:
                    while True:
                        data = f.read(2048)
                        if data == b'':
                            break
                        socket_receive.sendall(data)

            udp_addr = file_info.get("udp_address")
            print(f"[{username}] downloaded file {file_name} from thread {thread_name} successfully.")

    except Exception as e:
        print(f"[{username}] fail to {type} the file {file_name}")
        msg = f"Transimssion failed due to server error"
        udp_Socket.sendto(msg.encode(), addr)
    finally:
        socket_receive.close()
        file_user_container.pop(IP, None)
        print(f"TCP connection with user: {username} {addr} closed.")

# Handle UDP client's file transfer request
def handle_upload_command(username, thread_name, file_name):    
    """
    Handle a single TCP file Upload session.
    """
    print(f"[{username}] Try to upload file: {file_name} to thread: {thread_name}")
    if not os.path.exists(thread_name):
        print(f"[{username}]'s Thread {thread_name} does not exist.")
        return f"Thread {thread_name} does not exist."
    
    if os.path.exists(thread_name+ '-' + file_name):
        print(f"[{username}] File {file_name} already exists ")
        return f"File {file_name} already exists in thread {thread_name}."
    
    print(f"[{username}] File {file_name} is ready to upload.")
    return f"Ready to upload file."

#Handle download command
def handle_download_command(username, thread_name, file_name):
    """
    Handle a single TCP file download session.
    """
    print(f"[{username}] Try to download file: {file_name} from thread: {thread_name}")
    if not os.path.exists(thread_name):
        print(f"[{username}]'s Thread {thread_name} does not exist.")
        return f"Thread {thread_name} does not exist."
    
    if not os.path.exists(thread_name+ '-' + file_name):
        print(f"[{username}] File {file_name} does not exist in thread {thread_name}.")
        return f"File not exists, please check the file name."
    
    print(f"[{username}]'s File {file_name} is ready to download.")
    return f"Ready to download file."

# ==== Handle UDP message ====
def handle_udp_message(data, clientAddress):

    """
    Process a UDP message (one of the 8 commands).
    """
    message = data.decode().strip()
    print(f"[UDP recv from {clientAddress}] {message}")

    creds = handle_credentials_file()
    response = ""
    #If user has not logged in, handle login request
    if clientAddress not in active_users:
        if clientAddress not in client_states:
            client_states[clientAddress] = {"stage": "waiting_username"}

        state = client_states[clientAddress]

        if state["stage"] == "waiting_username":
            username = message
            if username in active_users.values():
                print(f"[{clientAddress}] User {username} already logged in.")
                response = "User already logged in. Please try again."
            elif username in creds:
                state['stage'] = "waiting_password"
                state['username'] = username
                print(f"detect {username} ,waiting for password")
                response = "Please enter your password:"
            else:
                state['stage'] = 'new_user'
                state['username'] = username
                print(f"[{clientAddress}] New user {username} trying to register.")
                response = "New user. Please enter your password:"

        elif state["stage"] == "waiting_password":
            password = message
            username = state['username']
            if creds.get(username) == password:
                active_users[clientAddress] = username
                print(f"[{clientAddress}] User {username} logged in successfully.")
                response = f"Login successful. Welcome {username}!"
                client_states.pop(clientAddress, None)
            else:
                print(f"[{clientAddress}] Incorrect password for user {username}.")
                response = "Incorrect password. Please try again."

        elif state["stage"] == "new_user":
            password = message
            username = state['username']
            append_credentials_file(username, password)
            active_users[clientAddress] = username
            print(f"[{clientAddress}] New user {username} registered successfully.")
            response = f"New user registered successfully. Welcome {username}!"
            client_states.pop(clientAddress, None)

    else:
        tokens = message.split()
        command = tokens[0]

        if command == "CRT":
            thread_name = tokens[1]
            username = active_users.get(clientAddress)
            response = handle_create_thread_command(username, thread_name)

        elif command == "MSG":
            thread_name = tokens[1]
            message = " ".join(tokens[2:])
            message = message.strip()
            username = active_users.get(clientAddress)
            response = handle_post_message_command(username, thread_name, message)

        elif  command == "DLT":
            thread_name = tokens[1]
            message_number = tokens[2]
            username = active_users.get(clientAddress)
            response = handle_delete_message_command(username, thread_name, message_number)
        
        elif  command == "EDT":
            thread_name = tokens[1]
            message_number = tokens[2]
            new_message = " ".join(tokens[3:])
            username = active_users.get(clientAddress)
            response = handle_edit_thread_command(username, thread_name, message_number, new_message)
        
        elif command == "LST":
            username = active_users.get(clientAddress)
            response = handle_list_thread_command(username)

        elif command == "RDT":
            thread_name = tokens[1]
            username = active_users.get(clientAddress)
            response = handle_read_thread_command(username, thread_name)
        
        elif command == "RMV":
            thread_name = tokens[1]
            username = active_users.get(clientAddress)
            response = handle_delete_thread_command(username, thread_name)
        
        elif command == "XIT":
            username = active_users.get(clientAddress)
            response = handle_exit_command(username, clientAddress)

        elif command == "UPD":
            thread_name = tokens[1]
            file_name = tokens[2]
            username = active_users.get(clientAddress)
            client_IP = clientAddress[0]
            result = handle_upload_command(username, thread_name, file_name)
            if result == "Ready to upload file.":
                file_user_container[client_IP] = {"username": username,"thread_name": thread_name,"file_name": file_name, "type": "upload","udp_address": clientAddress}
                response_msg = f"File name checked, ready for TCP connection"
                udp_Socket.sendto(response_msg.encode(), clientAddress)
            else:
                udp_Socket.sendto(result.encode(), clientAddress)
                
            return 

        elif command == "DWN":
            thread_name = tokens[1]
            file_name = tokens[2]
            username = active_users.get(clientAddress)
            client_IP = clientAddress[0]
            result = handle_download_command(username, thread_name, file_name)
            if result == "Ready to download file.":
                file_user_container[client_IP] = {"username": username,"thread_name": thread_name,"file_name": file_name, "type": "download","udp_address": clientAddress}
                response_msg = f"File exists, ready for TCP connection"
                udp_Socket.sendto(response_msg.encode(), clientAddress)
            else:
                udp_Socket.sendto(result.encode(), clientAddress)
                
            return


    udp_Socket.sendto(response.encode(), clientAddress)


# Main server loop
def main_server():
    """
    Main loop to handle both UDP and TCP sockets using select().
    """
    sockets_list = [udp_Socket, tcp_Socket]

    while True:
        sockets_received, _, _ = select.select(sockets_list, [], [])

        for sock in sockets_received:
            if sock == udp_Socket:
                # Receive and handle UDP message
                data, clientAddress = udp_Socket.recvfrom(2048)
                t = threading.Thread(target=handle_udp_message, args=(data, clientAddress))
                t.start()

            elif sock == tcp_Socket:
                # Accept TCP connection and handle file transfer in a new thread
                socket, addr = tcp_Socket.accept()
                t = threading.Thread(target=handle_tcp_file_transfer, args=(socket, addr))
                t.start()


# ==== Start server ====
if __name__ == "__main__":
    main_server()
