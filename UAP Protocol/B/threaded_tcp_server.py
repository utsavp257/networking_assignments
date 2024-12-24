import socket
import threading

clients = []  # List to store all connected client sockets

# Function for handling incoming messages from clients
def handle_client(client_socket, addr):
    print(f"New connection from {addr}")
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data or data.lower() == 'exit':  # Client wants to disconnect
                print(f"Client {addr} disconnected.")
                clients.remove(client_socket)
                client_socket.close()
                break
            print(f"Received from {addr}: {data}")
            broadcast(f"Message from {addr}: {data}", client_socket)
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            clients.remove(client_socket)
            client_socket.close()
            break

# Function to broadcast messages to all connected clients
def broadcast(message, sender_socket=None):
    for client in clients:
        if client != sender_socket:  # Avoid sending to the sender itself
            try:
                client.sendall(message.encode())
            except Exception as e:
                print(f"Error broadcasting to a client: {e}")
                clients.remove(client)
                client.close()

def main():
    server_host = '127.0.0.1'  # Localhost
    server_port = 12345

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)
    print(f"Server listening on {server_host}:{server_port}")

    while True:
        client_socket, addr = server_socket.accept()
        clients.append(client_socket)

        # Start a thread for each connected client
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == "__main__":
    main()
