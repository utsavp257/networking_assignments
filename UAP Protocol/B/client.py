#! /usr/bin/python3
import asyncio
import struct
import random
import sys
import aiofiles
import time

MAGIC = 0xC461
VERSION = 1
COMMANDS = {'HELLO': 0, 'DATA': 1, 'ALIVE': 2, 'GOODBYE': 3}
TIMEOUT = 1000  

class UAPClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, client):
        self.client = client
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.client.handle_response(data)

    def error_received(self, exc):
        print(f"Error received: {exc}")
        self.client.running = False

    def connection_lost(self, exc):
        print(f"Hit enter to quit")
        self.client.running = False

class UAPClient:
    def __init__(self, hostname, port, input_file=None):
        self.server_address = (hostname, port)
        self.input_file = input_file
        self.session_id = random.randint(1, 0xFFFFFFFF)
        self.seq_number = 0
        self.running = True
        self.timer_task = None
        self.logical_clock = 0
        self.outputFlag = 0

    def create_packet(self, command, data=''):
        self.logical_clock += 1
        packet = struct.pack('>HBBIIQ', MAGIC, VERSION, command, self.seq_number, self.session_id, self.logical_clock)
        if data:
            packet += data.encode('utf-8', errors='ignore')
        return packet

    async def send_hello(self, transport):
        print("Sending HELLO...")
        packet = self.create_packet(COMMANDS['HELLO'])
        transport.sendto(packet, self.server_address)
        self.seq_number += 1

    async def send_goodbye(self, transport):
        print("Sending GOODBYE...")
        packet = self.create_packet(COMMANDS['GOODBYE'])
        transport.sendto(packet, self.server_address)
        self.seq_number += 1
        self.running = False

    async def send_data(self, data, transport):
        packet = self.create_packet(COMMANDS['DATA'], data)
        transport.sendto(packet, self.server_address)
        self.seq_number += 1

    def handle_response(self, data):
        packet = self.parse_packet(data)
        new_logical_clock = packet['logical_clock']
        self.logical_clock = new_logical_clock + 1
        if packet and packet['magic'] == MAGIC:
            command_name = self.get_command_name(packet['command'])
            if self.outputFlag == 0:
            	print(f"Received {command_name} from server")
            if packet['command'] == COMMANDS['GOODBYE']:
                print("Closing connection...")
                self.running = False
            else:
                self.reset_timer()

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

    async def input_handler(self, transport):
        if self.input_file:
            async with aiofiles.open(self.input_file, 'r', encoding='utf-8') as file:
                async for line in file:
                    line = line.strip()
                    if line:
                        await self.send_data(line, transport)
                print("Waiting 3 seconds for server to finish printing")
                time.sleep(3)
                await self.send_goodbye(transport)
                print("EOF reached. Goodbye sent. Closing connection...")
                self.outputFlag = 1
        else:
            while self.running:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                line = line.strip()
                if line == 'q':
                    await self.send_goodbye(transport)
                    break
                await self.send_data(line, transport)

    async def start_timer(self, transport):
        try:
            await asyncio.sleep(TIMEOUT)
            print("Timeout reached. Sending GOODBYE...")
            self.running = False  
        except asyncio.CancelledError:
            pass

    def reset_timer(self):
        if self.timer_task:
            self.timer_task.cancel()
        self.timer_task = asyncio.create_task(self.start_timer(self.transport))

    async def start(self):
        loop = asyncio.get_running_loop()
        self.protocol = UAPClientProtocol(self)
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: self.protocol,
            remote_addr=self.server_address
        )


        await self.send_hello(self.transport)
        self.reset_timer()


        input_task = asyncio.create_task(self.input_handler(self.transport))

        while self.running:
            await asyncio.sleep(1)


        self.transport.close()

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python client.py <hostname> <portnum> [inputfile]")
        sys.exit(1)

    hostname = sys.argv[1]
    portnum = int(sys.argv[2])
    input_file = sys.argv[3] if len(sys.argv) == 4 else None

    client = UAPClient(hostname, portnum, input_file)
    asyncio.run(client.start())
