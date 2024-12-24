import asyncio
import socket

class AsyncServer:
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("", port))
        self.server_socket.listen()
        self.server_socket.setblocking(False)

    async def listen_for_connections(self):
        print(f"Server listening on port {self.port}")
        while True:
            client_socket, address = await asyncio.get_running_loop().sock_accept(self.server_socket)
            print(f"Accepted connection from {address}")
            asyncio.create_task(self.handle_client(client_socket, address))

    async def handle_client(self, client_socket, address):
        print(f"Connection established with {address}")
        try:
            while True:
                data = await asyncio.get_running_loop().sock_recv(client_socket, 1024)
                if not data:
                    print(f"Connection closed by {address}")
                    break

                message = data.decode().strip()
                print(f"Received from {address}: {message}")

                if message == "SEND GOODBYE":
                    response = "GOODBYE"
                    await asyncio.get_running_loop().sock_sendall(client_socket, response.encode())
                    print(f"Sent to {address}: {response}")
                    break
                else:
                    response = "answer"
                    await asyncio.get_running_loop().sock_sendall(client_socket, response.encode())
                    print(f"Sent to {address}: {response}")
        except Exception as e:
            print(f"Error with client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Closed connection with {address}")

    async def start(self):
        await self.listen_for_connections()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <portnum>")
        sys.exit(1)

    port = int(sys.argv[1])
    server = AsyncServer(port)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server interrupted.")
import asyncio
import socket

class AsyncServer:
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("", port))
        self.server_socket.listen()
        self.server_socket.setblocking(False)

    async def listen_for_connections(self):
        print(f"Server listening on port {self.port}")
        while True:
            client_socket, address = await asyncio.get_running_loop().sock_accept(self.server_socket)
            print(f"Accepted connection from {address}")
            asyncio.create_task(self.handle_client(client_socket, address))

    async def handle_client(self, client_socket, address):
        print(f"Connection established with {address}")
        try:
            while True:
                data = await asyncio.get_running_loop().sock_recv(client_socket, 1024)
                if not data:
                    print(f"Connection closed by {address}")
                    break

                message = data.decode().strip()
                print(f"Received from {address}: {message}")

                if message == "SEND GOODBYE":
                    response = "GOODBYE"
                    await asyncio.get_running_loop().sock_sendall(client_socket, response.encode())
                    print(f"Sent to {address}: {response}")
                    break
                else:
                    response = "answer"
                    await asyncio.get_running_loop().sock_sendall(client_socket, response.encode())
                    print(f"Sent to {address}: {response}")
        except Exception as e:
            print(f"Error with client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Closed connection with {address}")

    async def start(self):
        await self.listen_for_connections()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <portnum>")
        sys.exit(1)

    port = int(sys.argv[1])
    server = AsyncServer(port)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server interrupted.")
