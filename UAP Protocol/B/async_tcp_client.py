import asyncio
import socket

from asyncio.tasks import gather

class AsynClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.server_address = (host, port)
        self.loop = asyncio.get_event_loop()
    
    async def listen_for_responses(self):
        while True:
            try:
                data = await asyncio.get_running_loop().sock_recv(self.client_socket, 1024)
                if not data:
                    print("Server closed the connection.")
                    break
                print(f"Received: {data.decode()}")
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
            
    async def handle_user_input(self):
        while True:
            try:
                input_msg = await asyncio.get_running_loop().run_in_executor(None, input, "> ")
                await asyncio.get_running_loop().sock_sendall(self.client_socket, input_msg.encode())
                print(f"Sent message: {input_msg}")
            except Exception as e:
                print(f"Error sending message: {e}")
                break

    async def start(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setblocking(False)

        try:
            await asyncio.get_running_loop().sock_connect(self.client_socket, (self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            
            await asyncio.gather(
                self.listen_for_responses(),
                self.handle_user_input()
            )
        except Exception as e:
            print(f"Error starting client: {e}")
        finally:
            self.client_socket.close()
            print("Connection closed.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <hostname> <portnum>")
        sys.exit(1)
   
    hostname = sys.argv[1]
    port = int(sys.argv[2])

    client = AsynClient(hostname, port)

    try:
        asyncio.run(client.start())
    except:
        print("error in starting client")
