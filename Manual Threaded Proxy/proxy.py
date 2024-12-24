"""
This script implements an HTTP/HTTPS proxy server.
Usage:
   - python proxy.py <port>
   - While creating proxy on the browser the host should be localhost i.e. 127.0.0.1 and port number-the one that is given as input as shown in the previous point. (We had some issue with windows blocking the IP 0.0.0.0)
Example:
    python proxy.py 8080

Requirements:
- The script listens on the specified <port> for incoming HTTP/HTTPS requests.
- It forwards these requests to the intended destination, relaying the responses back to the client.
- Supports HTTP CONNECT tunneling for HTTPS traffic.

Ensure that the port number is between 1024 and 65535.
"""



import threading
import socket
import sys
from datetime import datetime

class Forward(threading.Thread):
    def __init__(self, sender, receiver):
        threading.Thread.__init__(self)
        self.sender = sender
        self.receiver = receiver

    def run(self):
        try:
            while True:
                data = self.sender.recv(4096)
                if not data:
                    break
                self.receiver.sendall(data)
        except socket.error:
            pass
        finally:
            self.sender.close()
            self.receiver.close()

class HttpHeader:
    def __init__(self, req):
        self.request = req

    def getStartLine(self):
        idx = self.request.find('\n')
        if idx == -1:
            idx = len(self.request)
        return self.request[:idx]

    def getHostLine(self):
        idx = self.request.lower().find('host')
        if idx == -1:
            return None
        tmp = self.request[idx:]
        idx2 = tmp.find('\n')
        return tmp[:idx2]

    def transformRequestHeader(self):
        tmp = self.request.replace('/1.1', '/1.0').replace('keep-alive', 'close')
        return HttpHeader(tmp)

    def isConnect(self):
        return 'connect ' in self.request.lower()

    def getRequest(self):
        return self.request

    def getVersion(self):
        idx = self.request.lower().find('http/')
        return self.request[idx:idx+8]

    def getHost(self):
        hostline = self.getHostLine()
        if hostline is None:
            return hostline
        host = hostline[5:].strip()  
        if host.startswith('http://'):
            host = host[7:]
        elif host.startswith('https://'):
            host = host[8:]
        host = host.strip()
        if '/' in host:
            host = host.split('/')[0]
        return host

    @staticmethod
    def printDateStamp():
        time = datetime.now().strftime("%d %B %H:%M:%S - ")
        print(time, end='')

class Proxy(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.connection = connection
        self.TIMEOUT = 20

    def parsePortNum(self, request):
        hostLine = request.getHostLine()
        if hostLine is None:
            return 80
        hostAndPort = hostLine[5:].strip()  
        if ':' in hostAndPort:
            parts = hostAndPort.split(':', 1)
            try:
                port = int(parts[1].split('/')[0])
                return port
            except ValueError:
                pass
        if request.getStartLine().lower().startswith('connect '):
            return 443
        else:
            return 80

    def run(self):
        try:
            request_bytes = b''
            self.connection.settimeout(self.TIMEOUT)
            while True:
                data = self.connection.recv(2048)
                if not data:
                    break
                request_bytes += data
                if b'\r\n\r\n' in request_bytes or b'\n\n' in request_bytes:
                    break

            if not request_bytes:
                self.connection.close()
                return

            requestString = request_bytes.decode('utf-8', errors='replace')
            request = HttpHeader(requestString)

            print(requestString)
            print("---------------")
            print(request)
            print("---------------")

            host = request.getHost()
            if host is None:
                return

            HttpHeader.printDateStamp()
            print(">>> " + request.getStartLine())
            print("---------------")

            port = self.parsePortNum(request)

            print(host)
            print("---------------")
            
            if '@' in host:
                host = host.split('@')[-1]

            print(host)
            print("---------------")

            
            host = host.strip('/')
            
            if ':' in host:
                host = host.split(':')[0]

            print(host)
            print("---------------")

            
            proxyToServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                proxyToServer.connect((host, port))
                proxyToServer.settimeout(self.TIMEOUT)
            except socket.error:
                responseToBrowser = request.getVersion() + ' 502 Bad Gateway\r\n\r\n'
                self.connection.sendall(responseToBrowser.encode())
                return

            if not request.isConnect():
                
                request = request.transformRequestHeader()
                data = request.getRequest().encode()
                
                proxyToServer.sendall(data)
                
                forward = Forward(proxyToServer, self.connection)
                forward.start()
                forward.join() 
            else:
                
                self.connection.sendall(b'HTTP/1.0 200 OK\r\n\r\n')
                
                readFromServer = Forward(proxyToServer, self.connection)
                readFromClient = Forward(self.connection, proxyToServer)
                readFromClient.start()
                readFromServer.start()
                readFromClient.join()  
                readFromServer.join()
        except socket.error:
            pass
        finally:
            
            self.connection.close()

def main():
    if len(sys.argv) != 2:
        print('Usage: python proxy.py <port>')
        sys.exit(1)

    port = int(sys.argv[1])
    if port > 65535 or port < 1024:
        raise ValueError('Invalid port number')

    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(("0.0.0.0", port))
        serverSocket.listen(5)
        HttpHeader.printDateStamp()
        print("Proxy listening on port " + str(port))
        while True:
            try:
                connection, addr = serverSocket.accept()
                task = Proxy(connection)
                task.start()
            except socket.error:
                pass
    except socket.error:
        print("Couldn't start server")
        sys.exit(1)

if __name__ == '__main__':
    main()
