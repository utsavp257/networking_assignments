#!/usr/bin/python3

import socket
import struct
import threading
import random
import sys
import time

MAGIC = 0xC461
VERSION = 1
COMMANDS = {'HELLO': 0, 'DATA': 1, 'ALIVE': 2, 'GOODBYE': 3}
TIMEOUT = 1000  

class UAPClient:
    def __init__(self, hostname, port, input_file=None):
        self.server_address = (hostname, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.01)  
        self.session_id = random.randint(1, 0xFFFFFFFF)
        self.seq_number = 0
        self.logical_clock = 0
        self.input_file = input_file
        self.shutdown_event = threading.Event()  
        self.last_received_time = time.time()  

    def create_packet(self, command, data=''):
        self.logical_clock += 1
        packet = struct.pack('>HBBIIQ', MAGIC, VERSION, command, self.seq_number, self.session_id, self.logical_clock)
        if data:
            packet += data.encode('utf-8', errors='ignore')
        return packet

    def send_hello(self):
        print("Sending HELLO...")
        packet = self.create_packet(COMMANDS['HELLO'])
        self.sock.sendto(packet, self.server_address)
        self.seq_number += 1

    def send_goodbye(self):
        try:
        	print("Sending GOODBYE...")
            packet = self.create_packet(COMMANDS['GOODBYE'])
            self.sock.sendto(packet, self.server_address)
        	self.seq_number += 1
        except OSError:
        	pass	

    def send_data(self, data):
        try:
        	packet = self.create_packet(COMMANDS['DATA'], data)
        	self.sock.sendto(packet, self.server_address)
        	self.seq_number += 1
        except OSError:
        	pass

    def listen(self):

        while not self.shutdown_event.is_set():
            try:
                data, _ = self.sock.recvfrom(4096)
                self.last_received_time = time.time()
                self.handle_response(data)
            except socket.timeout:
                continue
            except OSError:
               
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                self.shutdown_event.set()
                break

    def handle_response(self, data):
        packet = self.parse_packet(data)
        new_logical_clock = packet['logical_clock']
        self.logical_clock = new_logical_clock + 1
        if packet and packet['magic'] == MAGIC:
            command_name = self.get_command_name(packet['command'])
            print(f"Received {command_name} from server")
            if packet['command'] == COMMANDS['GOODBYE']:
                print("Closing connection...")
                self.shutdown_event.set()  
                self.sock.close()  
                return

    def parse_packet(self, packet):
        try:
            magic, version, command, seq_number, session_id, logical_clock = struct.unpack('>HBBIIQ', packet[:20])
            data = packet[20:].decode('utf-8')
            return {'magic': magic, 'version': version, 'command': command, 'seq_number': seq_number, 'session_id': session_id, 'data': data, 'logical_clock': logical_clock}
        except struct.error:
            return None

    def get_command_name(self, command):
        for cmd, value in COMMANDS.items():
            if value == command:
                return cmd
        return "UNKNOWN"

    def input_handler(self):
        if self.input_file:
            with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    if self.shutdown_event.is_set():
                        break
                    line = line.strip()
                    if line:
                        self.send_data(line)
                time.sleep(5)
                self.send_goodbye()
                print("EOF reached. Goodbye sent. Closing connection...")
        else:
            while not self.shutdown_event.is_set():
                try:
                    line = sys.stdin.readline()  
                    if line == '':  
                        self.send_goodbye()
                        break
                    line = line.strip()
                    if line == 'q':
                        self.send_goodbye()
                        break
                    self.send_data(line)  
                except KeyboardInterrupt:  
                    self.send_goodbye()
                    break

    def timeout_monitor(self):
        while not self.shutdown_event.is_set():
            time.sleep(1)  
            if time.time() - self.last_received_time > TIMEOUT:
                print("Timeout reached. No response from the server. Quitting the client...")
                self.shutdown_event.set()  
                self.sock.close()  

    def start(self):
        
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()

        
        timeout_thread = threading.Thread(target=self.timeout_monitor)
        timeout_thread.start()

        
        self.send_hello()

        
        self.input_handler()

        
        listen_thread.join()
        timeout_thread.join()

        
        if not self.sock._closed:
            self.sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: ./client <hostname> <portnum> [inputfile]")
        sys.exit(1)

    hostname = sys.argv[1]
    portnum = int(sys.argv[2])
    input_file = sys.argv[3] if len(sys.argv) == 4 else None

    client = UAPClient(hostname, portnum, input_file)
    client.start()
