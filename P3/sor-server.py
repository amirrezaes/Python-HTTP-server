import socket
import sys
import re
import time
import struct
import queue
import logging
import select
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s', datefmt='%a %b %d %H:%M:%S %Z %Y')
# Constants
CLOSED = "CLOSED"
SYNC = "SYNC"
SYNC_RCV = "SYNC_RCV"
SYNC_SENT = "SYNC_SENT"
CONNECTED = "CONNECTED"
OPEN = "OPEN"
FINISH = "FINISH"
FIN_RCV = "FIN_RCV"
FIN_SENT = "FIN_SENT"
CON_FIN_RCVD = "CON_FIN_RCVD"
RESET = "RESET"
TIMEOUT = 30

RDP_SEGMENT = 0
HTTP_SEGMENT = 1
FILE_SEGMENT = 2

RDP_COMMAND = 0
ACK_NUMBER = 1

PACKET_SIZE = 1024
SEQ_NUM_RANGE = 2**32

STRUCT_FMT = "!3sI"
STRUCT_FMT_RECV = "!15sI"

timer = time.time()

server_ip_address, server_udp_port_number, server_buffer_size, server_payload_length = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # create a UDP/IP socket
server.setblocking(False)
server_address = (server_ip_address, server_udp_port_number)
server.bind(server_address) # Bind the socket to the port

connected_clients = {} #address:Client
message_queues = {} # Outgoing message queues (socket:Queue)


def reformat(data: bytes) -> bytes:
    splited = data.split(b"\n\n")
    if len(splited) > 1:
        return struct.pack(STRUCT_FMT, splited[0]) + b"\n\n".join(splited[1:])
    else:
        return struct.pack(STRUCT_FMT, splited[0])

class Client:
    def __init__(self, ip_port: tuple) -> None:
        self.ip_port = ip_port
        self.state = CLOSED
        self.seq_num = 0
        self.exp_ack_num = 0
        self.file: Dict[int, bytes] = {}
        self.http = None
        self.last_received = None
    
    def unpack_message(self, message: bytes) -> tuple:
        size = struct.calcsize(STRUCT_FMT)
        return struct.unpack(STRUCT_FMT, message[:size]), message[size:]
    
    def send_syn(self) -> None:
        self.last_received = time.time() # if sending syn, it means we have reveived a syn
        packet = struct.pack('!3sI', b"SYN", self.seq_num)
        sock.sendto(packet, self.ip_port)
        self.seq_num += 1
        self.exp_ack_num += 1

    def send_rst(self):
        self.last_received = time.time() # if sending rst, it means we have reveived a bad message
        packet = struct.pack('!3sI', b"RST", self.seq_num)
        sock.sendto(packet, self.ip_port)
        self.seq_num = 0
        self.exp_ack_num = 0
    
    def send_fin(self) -> None:
        self.last_received = time.time() # if sending fin, it means we have reveived a fin
        packet = struct.pack('!3sI', b"FIN", self.seq_num)
        sock.sendto(packet, self.ip_port)
        self.seq_num = 0
        self.exp_ack_num = 0
    
    def next_data(self) -> bytes:
        if self.seq_num > max(self.file.keys()):
            self.state = CON_FIN_RCVD
            return b""
        return self.file[self.seq_num]
        
    def send_data(self) -> None:
        data = self.next_data()
        if not data:
            return
        packet = struct.pack('!3sI', b"DAT", self.seq_num) + data

        # Send packet to receiver
        sock.sendto(packet, self.ip_port)

        # Wait for ACK from receiver with timeout of 1 second
        #self.recieve_ack(data)

    def recieve_ack(self, rdp_seg) -> None:
        #while True:
            #sock.settimeout(5)
        if rdp_seg[ACK_NUMBER] == self.exp_ack_num:
            self.last_received = time.time()
            print(f"expected ack: {self.exp_ack_num}, got: {rdp_seg[ACK_NUMBER]}")
            print("Packet", self.seq_num, "sent successfully")
            data_len = len(self.next_data()) or 1
            self.seq_num += data_len
            self.exp_ack_num += data_len
        #elif self.packet_timeout() or rdp_seg[ACK_NUMBER] != self.exp_ack_num:
        else:
            # send the last ack packet again
            self.seq_num = rdp_seg[ACK_NUMBER]
            #packet = struct.pack('!3sI', b"DAT", self.seq_num) + self.file[rdp_seg[ACK_NUMBER]]
            #sock.sendto(packet, self.ip_port)

    def split_file(self, name: str) -> Dict[int, bytes]:
        buffer = {}
        index = 1
        with open(name, "rb") as file:
            while (chunk:=file.read(PACKET_SIZE)) != b'':
                buffer[index] = chunk
                index += len(chunk)
        print("file split into: ", buffer.keys())
        return buffer

    def handle_data(self, http_data: bytes, file_data) -> None:
        if http_data:
            self.file = self.split_file(http_data.decode())
        if file_data:
            pass
        #print("clinet speaking: file is:", self.file)


    def timeout(self) -> bool:
        if self.last_received is None:
            return True
        return time.time() - self.last_received > TIMEOUT
    
    def packet_timeout(self) -> bool:
        if self.last_received is None:
            return False
        return time.time() - self.last_received > 1





def split_data(data: bytes) -> tuple:
    size = struct.calcsize(STRUCT_FMT_RECV)
    rdp_seg, rest= struct.unpack(STRUCT_FMT_RECV, data[:size]), data[size:]
    try:
        http_seg, file_seg = rest.split(b"\n\n")
    except ValueError: # if out of shape packege recived, unlikely to happen
        http_seg = b""
        file_seg = rest
    return (rdp_seg, http_seg, file_seg)


def state_decider(client: Client, data: bytes) -> None:
    data_seg = split_data(data)
    if client.state == CLOSED:
        print("clinet state: ", client.state, "rdp_seg: ", data_seg[RDP_SEGMENT])
        if b"SYN" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            print("recived SYN")
            client.state = SYNC_RCV
        elif b"ACk" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            message_queues[client].put(client.send_fin)

    if client.state == SYNC_RCV:
        print("clinet state: ", client.state, "rdp_seg: ", data_seg[RDP_SEGMENT])
        # send SYN|ACK
        if b"FIN" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            client.state = FIN_RCV
        else:
            message_queues[client].put(client.send_syn)
            client.state = SYNC_SENT

    if client.state == SYNC_SENT:
        print("clinet state: ", client.state, "rdp_seg: ", data_seg[RDP_SEGMENT])
        if b"ACK" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            client.state = CONNECTED

    if client.state == CONNECTED:
        #print("clinet state: ", client.state, "rdp_seg: ", data_seg[RDP_SEGMENT])
        if b"FIN" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            client.state = CON_FIN_RCVD
        elif b"DAT" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            client.handle_data(data_seg[HTTP_SEGMENT], data_seg[FILE_SEGMENT])
        if b"ACK" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            message_queues[client].put(client.send_data)
            message_queues[client].put((client.recieve_ack, data_seg[RDP_SEGMENT]))
            #input()
        elif b"SYN" in data_seg[RDP_SEGMENT][RDP_COMMAND]:
            client.state = CLOSED
            message_queues[client].put(client.send_rst)
    if client.state == FIN_SENT:
        print("clinet state: ", client.state, "rdp_seg: ", data_seg[RDP_SEGMENT])
        if b"ACK" in data_seg[RDP_SEGMENT][RDP_COMMAND] or client.timeout():
            client.state = CLOSED
    
    if client.state == CON_FIN_RCVD:
        print("clinet state: ", client.state, "rdp_seg: ", data_seg[RDP_SEGMENT])
        message_queues[client].put(client.send_fin)
        client.state = FIN_SENT

    if client.state == FIN_RCV:
        print("clinet state: ", client.state, "rdp_seg: ", data_seg[RDP_SEGMENT])
        message_queues[client].put(client.send_fin)
        client.state = FIN_SENT
        pass
    



while True:
    readable, writable, exceptional = select.select([server], [server], [server], TIMEOUT)
    for sock in readable:
        sock.settimeout(5)
        data, address = sock.recvfrom(PACKET_SIZE)
        if address not in connected_clients:
            new_client = Client(address)
            connected_clients[address]= new_client
            message_queues[new_client] = queue.Queue()

        state_decider(connected_clients[address], data)
            

    
    for sock in writable:
        for client in message_queues:
            try:
                next_msg = message_queues[client].get_nowait()
                if type(next_msg) == tuple:
                    next_msg[0](*next_msg[1:])
                else:
                    next_msg()
                timer = time.time()
            except queue.Empty: # No messages waiting from this client
                #connected_clients.pop(client.i)
                pass
            except:
                pass

        
    if time.time() - timer > TIMEOUT:
        break