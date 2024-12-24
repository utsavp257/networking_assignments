#! /usr/bin/python3

import socket
import struct
import threading
import time
import sys

MAGIC = 0xC461
VERSION = 1
COMMANDS = {'HELLO': 0, 'DATA': 1, 'ALIVE': 2, 'GOODBYE': 3}
REVERSE_COMMANDS = {v: k for k, v in COMMANDS.items()}
TIMEOUT_SECONDS = 1000  

class ServerState:
    def __init__(self):
        self.sessions = {}  
        self.shutdown_event = threading.Event()
        self.logical_clock = 0

    def increment_logical_clock(self):
        """Increments the global logical clock for the server."""
        with threading.Lock():
            self.logical_clock += 1
        return self.logical_clock


class UAPServer:
    def __init__(self, port, server_state):
        self.port = port
        self.server_state = server_state
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.lock = threading.Lock()
        self.closed_sessions = []

    def start(self):
        print(f"Waiting on port {self.port}...")
        self.listener_thread = threading.Thread(target=self.listen_for_packets, daemon=True)
        self.listener_thread.start()

        self.timeout_thread = threading.Thread(target=self.session_timeout_checker, daemon=True)
        self.timeout_thread.start()

        input_thread = threading.Thread(target=self.input_handler, daemon=True)
        input_thread.start()

        
        input_thread.join()

        
        self.server_state.shutdown_event.set()
        self.listener_thread.join()
        self.timeout_thread.join()

        print("Server has stopped.")
        sys.exit(0)

    def listen_for_packets(self):
        while not self.server_state.shutdown_event.is_set():
            try:
                self.sock.settimeout(1.0)  
                data, addr = self.sock.recvfrom(4096)
                threading.Thread(target=self.handle_packet, args=(data, addr), daemon=True).start()
            except socket.timeout:

                continue
            except Exception as e:
                print(f"Error receiving data: {e}")

    def handle_packet(self, data, addr):
        packet = self.parse_packet(data)

        if not packet or packet['magic'] != MAGIC:
            return  
            
        session_id = packet['session_id']
        seq_number = packet['seq_number']
        new_logical_clock = packet['logical_clock']

        current_time = time.time()
        idk = self.server_state.increment_logical_clock()


        with self.lock:
            if session_id not in self.server_state.sessions:
                if session_id in self.closed_sessions:
                    filtered_list = [item for item in self.closed_sessions if item != session_id]
                    self.closed_sessions[:] = filtered_list
                print(f"{hex(session_id)} [{seq_number}] Session created")
                self.server_state.sessions[session_id] = (addr, current_time, seq_number)
                self.send_packet(COMMANDS['ALIVE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)
                return
            
            addr, last_active, expected_seq_number = self.server_state.sessions[session_id]

            if seq_number == expected_seq_number-1:
                print(f"{hex(session_id)} [{seq_number}] Duplicate packet")
                return
            
            elif seq_number < expected_seq_number:
                print(f"{hex(session_id)} [{seq_number}] Protocol Error")
                print(f"{hex(session_id)} Session closed")
                self.send_packet(COMMANDS['GOODBYE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)

                del self.server_state.sessions[session_id]

            elif seq_number > expected_seq_number:

                for missing_seq in range(expected_seq_number, seq_number):
                    if missing_seq != 0:
                        print(f"{hex(session_id)} [{missing_seq}] Lost packet")

                self.server_state.sessions[session_id] = (addr, current_time, seq_number + 1)
            
            if packet['command'] == COMMANDS['HELLO']:
                self.send_packet(COMMANDS['ALIVE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)

            elif packet['command'] == COMMANDS['DATA']:
                if packet['data'].strip().lower() == 'q':
                    print(f"{hex(session_id)} [{seq_number}] Terminating session as requested by client")
                    self.send_packet(COMMANDS['GOODBYE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)
                    print(f"{hex(session_id)} Session closed")
                    del self.server_state.sessions[session_id]
                else:
                    print(f"{hex(session_id)} [{seq_number}] {packet['data']}")
                    self.server_state.sessions[session_id] = (addr, current_time, seq_number + 1)
                    self.send_packet(COMMANDS['ALIVE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)
                    
            elif packet['command'] == COMMANDS['GOODBYE']:
                print(f"{hex(session_id)} [{seq_number}] GOODBYE from client")
                print(f"{hex(session_id)} Session closed")
                self.send_packet(COMMANDS['GOODBYE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)
                del self.server_state.sessions[session_id]

    def send_packet(self, command, seq_number, session_id, logical_clock, addr, data=''):
        packet = self.create_packet(command, seq_number, session_id, logical_clock, data)
        try:
            self.sock.sendto(packet, addr)
            if(command==3):
                self.closed_sessions.append(session_id)
            print(f"Sent {REVERSE_COMMANDS.get(command, 'UNKNOWN')} to {addr}")
        except Exception as e:
            print(f"Error sending data: {e}")

    def create_packet(self, command, seq_number, session_id, logical_clock, data=''): #TODO check all calls for create_packet
        packet = struct.pack('>HBBIIQ', MAGIC, VERSION, command, seq_number, session_id, logical_clock)
        if data:
            packet += data.encode('utf-8')
        return packet

    def parse_packet(self, packet): 
        try:
            magic, version, command, seq_number, session_id, logical_clock = struct.unpack('>HBBIIQ', packet[:20])
            data = packet[20:].decode('utf-8')
            return {'magic': magic, 'version': version, 'command': command, 'seq_number': seq_number, 'session_id': session_id, 'data': data, 'logical_clock': logical_clock}
        except struct.error:
            return None

    def session_timeout_checker(self):
        idk = self.server_state.increment_logical_clock()
        while not self.server_state.shutdown_event.is_set():
            with self.lock:
                current_time = time.time()
                inactive_sessions = []

                for session_id, (addr, last_active, _) in self.server_state.sessions.items():
                    if current_time - last_active > TIMEOUT_SECONDS:
                        inactive_sessions.append(session_id)

                for session_id in inactive_sessions:
                    if session_id not in self.closed_sessions:
                        list_val = self.server_state.sessions[session_id]
                        self.send_packet(COMMANDS['GOODBYE'], 0, session_id, self.server_state.logical_clock, list_val[0])
                        print(f"{hex(session_id)} Session timed out due to inactivity. Sent GOODBYE to {list_val[0]}.")
                        del self.server_state.sessions[session_id]

            time.sleep(1)  

    def input_handler(self):
        try:
            while not self.server_state.shutdown_event.is_set():

                user_input = input().strip().lower()
                if user_input == 'q':
                    print("Shutting down server...")
                    self.server_state.shutdown_event.set()
                    self.terminate_all_sessions()
                    break
                    
        except:
            pass


    def terminate_all_sessions(self):
        idk = self.server_state.increment_logical_clock()

        with self.lock:
            for session_id, val_list in self.server_state.sessions.items():
                self.send_packet(COMMANDS['GOODBYE'], 0, session_id, self.server_state.logical_clock, val_list[0])
                print(f"{hex(session_id)} Terminating session. Sent GOODBYE to {val_list[0]}.")
            self.server_state.sessions.clear()
        print("All sessions terminated. Server is shutting down.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <portnum>")
        sys.exit(1)

    portnum = int(sys.argv[1])


    server_state = ServerState()


    server = UAPServer(portnum, server_state)
    server.start()
