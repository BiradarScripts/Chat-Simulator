import socket
import threading
import sys

clients = {}
clients_lock = threading.Lock()

def broadcast(message, room, origin_conn):
    with clients_lock:
        for conn, data in clients.items():
            if conn != origin_conn and data['room'] == room:
                try:
                    conn.sendall(message.encode('utf-8'))
                except socket.error:
                    pass 

def global_broadcast(message, origin_conn):
    with clients_lock:
        for conn in clients.keys(): 
            if conn != origin_conn:
                try:
                    conn.sendall(message.encode('utf-8'))
                except socket.error:
                    pass 

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    username = None
    current_room = "#general" 
    
    try:
        while True:
            login_data = conn.recv(1024).decode('utf-8').strip()
            if not login_data:
                return

            parts = login_data.split()
            login_success = False
            
            if len(parts) == 2 and parts[0] == "LOGIN":
                potential_username = parts[1]
                
                with clients_lock:
                    username_taken = False
                    for data in clients.values():
                        if data['username'] == potential_username:
                            username_taken = True
                            break
                    
                    if username_taken:
                        conn.sendall(b"ERR username-taken\n")
                    else:
                        username = potential_username
                        clients[conn] = {'username': username, 'room': current_room}
                        conn.sendall(b"OK\n")
                        print(f"[LOGIN] {addr} logged in as {username} in {current_room}")
                        login_success = True
            else:
                conn.sendall(b"ERR bad-login-format\n")

            if login_success:
                broadcast_msg = f"INFO {username} connected\n"
                broadcast(broadcast_msg, current_room, conn)
                break

        conn.settimeout(60.0) 

        while True:
            message_data = conn.recv(1024).decode('utf-8').strip()
            
            if not message_data:
                break 
                
            if message_data == "PING":
                conn.sendall(b"PONG\n")
                continue

            if message_data == "WHO":
                user_list = []
                with clients_lock:
                    user_list = [data['username'] for data in clients.values()]
                
                conn.sendall(b"INFO --- All Connected Users ---\n")
                for user in user_list:
                    conn.sendall(f"USER {user}\n".encode('utf-8'))
                conn.sendall(b"INFO --- End of List ---\n")
                continue

            if message_data == "RWHO":
                user_list = []
                with clients_lock:
                    for data in clients.values():
                        if data['room'] == current_room:
                            user_list.append(data['username'])
                
                conn.sendall(f"INFO --- Users in {current_room} ---\n".encode('utf-8'))
                for user in user_list:
                    conn.sendall(f"USER {user}\n".encode('utf-8'))
                conn.sendall(b"INFO --- End of List ---\n")
                continue
            
            if message_data == "LEAVE":
                if current_room == "#general":
                    conn.sendall(b"ERR already-in-general\n")
                    continue
                
                broadcast(f"INFO {username} left the room\n", current_room, conn)
                
                old_room = current_room
                current_room = "#general"
                with clients_lock:
                    clients[conn]['room'] = current_room
                
                conn.sendall(b"OK joined #general\n")
                broadcast(f"INFO {username} joined the room\n", current_room, conn)
                print(f"[ROOM] {username} left {old_room} and joined {current_room}")
                continue

            parts = message_data.split(maxsplit=1)
            command = parts[0]

            if command == "JOIN" and len(parts) == 2:
                new_room = parts[1].split()[0]
                if not new_room.startswith("#"):
                    conn.sendall(b"ERR bad-room-name (must start with #)\n")
                    continue
                
                if new_room == current_room:
                    conn.sendall(b"ERR already-in-that-room\n")
                    continue

                broadcast(f"INFO {username} left the room\n", current_room, conn)
                
                old_room = current_room
                current_room = new_room
                with clients_lock:
                    clients[conn]['room'] = current_room
                
                conn.sendall(f"OK joined {current_room}\n".encode('utf-8'))
                broadcast(f"INFO {username} joined the room\n", current_room, conn)
                print(f"[ROOM] {username} left {old_room} and joined {current_room}")
                continue

            if command == "GMSG" and len(parts) == 2:
                text = parts[1]
                broadcast_msg = f"[GLOBAL] {username}: {text}\n"
                global_broadcast(broadcast_msg, conn)
            
            elif command == "MSG" and len(parts) == 2:
                text = parts[1]
                broadcast_msg = f"MSG {username} {text}\n"
                broadcast(broadcast_msg, current_room, conn)
            
            elif command == "DM" and len(parts) == 2:
                dm_parts = parts[1].split(maxsplit=1)
                
                if len(dm_parts) == 2:
                    target_username = dm_parts[0]
                    text = dm_parts[1]
                    dm_msg = f"DM {username} {text}\n"
                    
                    target_conn = None
                    with clients_lock:
                        for c, data in clients.items():
                            if data['username'] == target_username:
                                target_conn = c
                                break
                    
                    if target_conn:
                        try:
                            target_conn.sendall(dm_msg.encode('utf-8'))
                        except socket.error:
                            conn.sendall(b"ERR failed-to-send\n")
                    else:
                        err_msg = f"ERR user-not-found {target_username}\n"
                        conn.sendall(err_msg.encode('utf-8'))
                else:
                    conn.sendall(b"ERR bad-dm-format\n")
            
            elif command == "NICK" and len(parts) == 2:
                new_username = parts[1].split()[0]
                old_username = username
                username_taken = False
                
                with clients_lock:
                    for data in clients.values():
                        if data['username'] == new_username:
                            username_taken = True
                            break
                    
                    if not username_taken:
                        clients[conn]['username'] = new_username
                        username = new_username 
                
                if username_taken:
                    conn.sendall(b"ERR nick-taken\n")
                else:
                    conn.sendall(b"OK nick-changed\n")
                    broadcast(f"INFO {old_username} is now known as {new_username}\n", current_room, conn)
            
            else:
                conn.sendall(b"ERR unknown-command\n")
    
    except socket.timeout:
        print(f"[TIMEOUT] {addr} (User: {username}) timed out.")
        try:
            conn.sendall(b"INFO idle-timeout\n")
        except socket.error:
            pass 

    except ConnectionResetError:
        print(f"[CONNECTION-RESET] {addr} (User: {username})")
    except Exception as e:
        print(f"[ERROR] {e}")
        
    finally:
        # 3. Disconnect Flow
        disconnect_msg = None
        room_to_notify = None
        
        if conn in clients:
            with clients_lock:
                if username:
                    room_to_notify = clients[conn]['room']
                    del clients[conn]
                    print(f"[DISCONNECT] {addr} (User: {username}) disconnected.")
                    disconnect_msg = f"INFO {username} disconnected\n"
        
        if disconnect_msg:
            broadcast(disconnect_msg, room_to_notify, conn)
        
        conn.close()

def start_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('', port))
        server_socket.listen(10) 
        print(f"[LISTENING] Server is listening on port {port}...")
        
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True 
            client_thread.start()

    except OSError as e:
        print(f"[SERVER-ERROR] {e}")
    finally:
        server_socket.close()
        print("[SHUTDOWN] Server is shutting down.")

if __name__ == "__main__":
    try:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    except ValueError:
        print("Invalid port number. Using default port 4000.")
        port = 4000
        
    start_server(port)