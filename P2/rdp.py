import select
import socket
import sys
import os
from time import time
from threading import Timer
import queue
import re
import logging
from typing import List

logging.basicConfig(level=logging.INFO,format='%(asctime)s: %(message)s', datefmt='%a %b %d %H:%M:%S %Z %Y')

CLOSED = "C"
SYNC = "S"
OPEN = "O"
FINISH = "F"
RESET = "R"

COMMAND = 0
HEADER = 1
PAYLOAD = 2

ACK = "ACK\n"
SYN = "SYN\n" 
DAT = "DAT\n"
FIN = "FIN\n"
RST = "RST\n"
EMPTY_LINE = "\n"
PACKET = "{comm}{h1}\n{h2}\n\n"

MAX_PAYLOAD_SIZE = 1024

ECHO_SERVER = ("165.232.76.174", 8888)

Sent = []
Recieved = {}

server_ip = sys.argv[1]
serverPort = int(sys.argv[2])
file_read = sys.argv[3]
file_write = sys.argv[4]
#echo_server = (os.getenv("h2"), 8888)
echo_server = ("127.0.0.1", 8888)
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setblocking(0)
# Bind the socket to the port
server_address = (server_ip, serverPort)
udp_sock.bind(server_address)
jobs = queue.Queue()
# request message

timeout = 30


class Tools:
    PATTERN = re.compile(r"(SYN|DAT|FIN|ACK|RST)\n(([a-zA-Z]+: [-1|\d]+\n)*)\n")

    def send(message: bytes, log: tuple):
        udp_sock.sendto(message, ECHO_SERVER)
        logging.info("Send; {}; {}; {}".format(*log))
        Sent.append((message, Timer))

    def good_packet(packet: bytes):
        packet = packet.decode()
        empty_pos = packet.find("\n\n")
        return "\n\n" != -1 and Tools.PATTERN.fullmatch(packet[:empty_pos+2])
    
    def recv():
        temp = udp_sock.recv(2048)
        if Tools.good_packet(temp):
            command, headers, payload = Tools.packet_splitter(temp)
        else:
            return ""
        logging.info("Receive; {}; {}; {}".format(command.strip(), *headers))
        return (command, headers, payload)

    def packet_splitter(packet: bytes):
        packet_enc = packet.decode()
        splited_packet = packet_enc.split("\n")
        command = splited_packet[0]
        headers = packet_enc[packet_enc.find("\n")+1:packet_enc.find("\n\n")].split("\n")
        payload = packet[packet.find(b"\n\n")+2:]
        return (command+"\n", [i for i in headers if i !=""], payload) # "\n" is for compatibility with Constants
    
    def send_rst():
        packet = "RST\n\n".encode()
        Tools.send(packet, ("RST", "", ""))

    def header_extractor(headers: List[str]):
        results = {}
        for h in headers:
            h = [i.strip().casefold() for i in h.split(":")]
            results[h[0]] = int(h[1])
        return results
    
    def file_read_split(name) -> dict:
        buffer = {}
        index = 1
        with open(name, "rb") as file:
            while (chunk:=file.read(MAX_PAYLOAD_SIZE)) != b'':
                buffer[index] = chunk
                index += len(chunk)
        return buffer

    def get_next_job():
        while True:
            try:
                jobs.get_nowait()() # run the job
            except queue.Empty:
                break
    def timeout(t):
        return time() - t >= 2



class Sender:


    def __init__(self, sock: socket.socket, file_chunks: List) -> None:
        self.socket = sock
        self.file: dict = file_chunks
        self.sent_file = {}
        self.state = CLOSED
        self.fin_state = False
        self.sequence = 0
        self.acked = 0
        self.reciver_window = 0
        self.on_air = {i:0 for i in self.file}
        self.send_syn() # make connection as soon as object is initialized

    def send_syn(self):
        h1 = f"Sequence: {self.sequence}"
        h2 = "Length: 0"
        packet = PACKET.format(comm=SYN, h1=h1, h2=h2).encode()
        Tools.send(packet, ("SYN", h1, h2))
        self.state = SYNC

    def reset(self):
        self.sequence = 0
        self.reciver_window = 0
        self.acked = 0
        self.state = RESET

    def rcv_ack(self, message: tuple):
        headers  = Tools.header_extractor(message[HEADER])
        self.reciver_window = headers["window"]
        self.acked = self.sequence = headers["acknowledgment"]
        self.state = self.fin_state and CLOSED or OPEN

    def send_data(self):
        if self.sequence != self.acked:
            print("packet lost\r")
            if Tools.timeout(self.on_air[self.acked]):
                self.sequence = self.acked
            else:
                return

        chunk = self.file.get(self.sequence)
        if chunk:
            h1 = f"Sequence: {self.sequence}"
            h2 = f"Length: {len(chunk)}"
            packet = PACKET.format(comm=DAT, h1=h1, h2=h2).encode()
            packet += chunk
            Tools.send(packet, ("DAT", h1, h2))
            self.on_air[self.sequence] = time()
            self.sequence += len(chunk)
        else:
            self.send_fin()


    def send_fin(self):
        h1 = f"Sequence: {self.sequence}"
        h2 = "Length: 0"
        packet = PACKET.format(comm=FIN, h1=h1, h2=h2).encode()
        Tools.send(packet, ("FIN", h1, h2))
        # TODO: find a way to put this at Finished first
        self.state = CLOSED
        self.fin_state = True

    def getstate(self):
        return self.state
    
    def timeout():
        pass



class Reciver:
    def __init__(self, sock: socket.socket) -> None:
        self.socket = sock
        self.rcv_buff: dict = {}
        self.state = CLOSED
        self.ack_number = 0
        self.window = 2048
    
    def send_ack(self):
        self.ack_number += 1
        h1 = f"Acknowledgment: {self.ack_number}"
        h2 = f"Window: {self.window}"
        packet = PACKET.format(comm=ACK, h1=h1, h2=h2).encode()
        Tools.send(packet, ("ACK", h1, h2))
        self.state = OPEN
    
    def rcv_data(self, message):
        headers = Tools.header_extractor(message[HEADER])
        if headers["sequence"] != self.ack_number:
            self.send_ack()
            return
        self.rcv_buff[headers["sequence"]] = message[PAYLOAD]
        self.ack_number += headers["length"] - 1 # send_ack will add 1 
        self.send_ack()

    def write_file(self):
        # TODO: wait for a while before closing
        self.state = CLOSED
        with open(file_write, 'wb') as file:
            for chunk in self.rcv_buff.values():
                file.write(chunk)


    
    def reset(self):
        self.ack_number = 0
        self.window = 2048
        self.state = RESET
    
    def getstate(self):
        return self.state
    

file_chunks = Tools.file_read_split(file_read)
print(file_chunks.keys())
rdp_receiver = Reciver(udp_sock)
rdp_sender = Sender(udp_sock, file_chunks)

while True:
    #if rdp_sender.getstate() == CLOSED:
    #    rdp_sender.send_syn()
    readable, writable, exceptional = select.select([udp_sock], [udp_sock], [udp_sock], timeout)
    if udp_sock in readable:
        message = Tools.recv()
        #print("raw_message:", message)
        #if the message in rcv_buf is complete (detect a new line):
        if not message:
            jobs.put(Tools.send_rst)
        else:
            #extract the message from rcv_buf, and split the message into RDP packets
            if message[COMMAND] == ACK:
                rdp_sender.rcv_ack(message)
            elif message[COMMAND] == SYN:
                jobs.put(rdp_receiver.send_ack)
            elif message[COMMAND] == DAT:
                rdp_receiver.rcv_data(message)
            elif message[COMMAND] == RST:
                rdp_receiver.reset()
                rdp_sender.reset()
                jobs.put(rdp_sender.send_syn)
            elif message[COMMAND] == FIN:
                rdp_receiver.write_file()
                jobs.put(rdp_receiver.send_ack)


    if udp_sock in writable:
        Tools.get_next_job()
        if rdp_receiver.state == OPEN and rdp_sender.state == OPEN:
            rdp_sender.send_data()
    else:
        print("still running")

    if udp_sock not in readable and udp_sock not in writable:
        if rdp_sender.getstate() == CLOSED and rdp_receiver.getstate() == CLOSED:
            break