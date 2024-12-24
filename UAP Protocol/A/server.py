#!/usr/bin/python3
import asyncio
import struct
import sys
import threading
import time

MAGIC = 0xC461
VERSION = 1
COMMANDS = {'HELLO': 0, 'DATA': 1, 'ALIVE': 2, 'GOODBYE': 3}
REVERSE_COMMANDS = {v: k for k, v in COMMANDS.items()}
TIMEOUT_SECONDS = 1000  

class ServerState:
    def __init__(self):
        
        self.sessions = {}
        self.shutdown_event = asyncio.Event()  
        self.logical_clock = 0

    def increment_logical_clock(self):
        """Increments the global logical clock for the server."""
        with threading.Lock():
            self.logical_clock += 1
        return self.logical_clock

class UAPServerProtocol:
    def __init__(self, server_state):
        self.server_state = server_state
        self.transport = None  
        self.ndp = 0

    def connection_made(self, transport):
        self.transport = transport  

    def datagram_received(self, data, addr):
        packet = self.parse_packet(data)

        if not packet or packet['magic'] != MAGIC:
            return  

        session_id = packet['session_id']
        seq_number = packet['seq_number']
        new_logical_clock = packet['logical_clock']
        current_time = time.time()
        idk = self.server_state.increment_logical_clock()

        if session_id not in self.server_state.sessions:
            print(f"{hex(session_id)} [{seq_number}] Session created")
            self.server_state.sessions[session_id] = (addr, current_time, seq_number)
            self.send_packet(COMMANDS['ALIVE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)
            return

        addr, last_active, expected_seq_number = self.server_state.sessions[session_id]

        if seq_number == expected_seq_number -1:
            print(f"{hex(session_id)} [{seq_number}] Duplicate packet")
            return
        
        elif seq_number < expected_seq_number :
            print(f"{hex(session_id)} [{seq_number}] Protocol Error")
            print(f"{hex(session_id)} Session closed")
            
            self.send_packet(COMMANDS['GOODBYE'], seq_number + 1, session_id, self.server_state.logical_clock, addr)
            del self.server_state.sessions[session_id]

        elif seq_number > expected_seq_number:
            
            for missing_seq in range(expected_seq_number, seq_number):
                if missing_seq!=0:
                    print(f"{hex(session_id)} [{missing_seq}] Lost packet")
                    self.ndp += 1

            
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
        self.transport.sendto(packet, addr)  
        if command != COMMANDS['GOODBYE']:
            print(f"Sent {REVERSE_COMMANDS.get(command, 'UNKNOWN')} to {addr}")

    def create_packet(self, command, seq_number, session_id, logical_clock, data=''):
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

    def connection_lost(self, exc):
        """Handle connection loss (e.g., when transport is closed)."""
        if exc:
            print(f"Connection lost due to error: {exc}")
        else:
            print("Connection closed.")

async def session_timeout_checker(server_state, protocol):
    """Periodically check for inactive sessions and close them if they exceed the timeout period."""
    while not server_state.shutdown_event.is_set():
        current_time = time.time()
        inactive_sessions = []

        
        for session_id, (addr, last_active, _) in server_state.sessions.items():
            if current_time - last_active > TIMEOUT_SECONDS:
                inactive_sessions.append(session_id)

        
        for session_id in inactive_sessions:
            list_val = server_state.sessions[session_id]
            protocol.send_packet(COMMANDS['GOODBYE'], 0, session_id, server_state.logical_clock, list_val[0])
            print(f"{hex(session_id)} Session timed out due to inactivity. Sent GOODBYE to {list_val[0]}.")
            del server_state.sessions[session_id]

        await asyncio.sleep(1)  

async def main(port, server_state):
    print(f"Waiting on port {port}...")
    loop = asyncio.get_running_loop()

    
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UAPServerProtocol(server_state),
        local_addr=('0.0.0.0', port)
    )

    
    asyncio.create_task(session_timeout_checker(server_state, protocol))

    try:
        await server_state.shutdown_event.wait()  
    finally:
        
        print("Shutting down server...")
        for session_id, val_list in server_state.sessions.items():
            protocol.send_packet(COMMANDS['GOODBYE'], 0, session_id, server_state.logical_clock, val_list[0])
            print(f"Sent GOODBYE to {val_list[0]}")

        
        await asyncio.sleep(1)

        
        transport.close()

def input_handler(server_state):
    while True:
        user_input = input()
        if user_input.strip().lower() == 'q':
            
            server_state.shutdown_event.set()  
            break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./server <portnum>")
        sys.exit(1)

    portnum = int(sys.argv[1])

    
    server_state = ServerState()

    
    input_thread = threading.Thread(target=input_handler, args=(server_state,), daemon=True)
    input_thread.start()

    
    asyncio.run(main(portnum, server_state))
