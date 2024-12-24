import socket
import threading

# Client listening for messages from the server
def listen_to_server(sock):
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                print("Server disconnected.")
                break
            print(f"Server: {data}")
        except Exception as e:
            print(f"Error listening to server: {e}")
            break

# Client sending user input to the server
def send_to_server(sock):
    while True:
        try:
            message = input("You: ")
            if message.lower() == 'exit':  # Command to close the connection
                sock.sendall(message.encode())
                print("Exiting...")
                break
            sock.sendall(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")
            break

def main():
    server_host = '127.0.0.1'  # Localhost
    server_port = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    print("Connected to the server. Type 'exit' to disconnect.")

    # Start threads for listening and sending
    threading.Thread(target=listen_to_server, args=(client_socket,), daemon=True).start()
    threading.Thread(target=send_to_server, args=(client_socket,)).start()

if __name__ == "__main__":
    main()
