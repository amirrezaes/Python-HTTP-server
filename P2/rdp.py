import select
import socket
import sys
import os
import queue
import re
import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s: %(message)s', datefmt='%a %b %d %H:%M:%S %Z %Y')

CLOSED = "C"
SYNC = "S"
OPEN = "O"
FINISH = "F"

ACK = "ACK\n"
SYN = "SYN\n" 
DAT = "DAT\n"
FIN = "FIN\n"
RST = "RST\n"
EMPTY_LINE = "\n"
PACKET = "{comm}{h1}\n{h2}\n\n"

MAX_PAYLOAD_SIZE = 1024

ECHO_SERVER = ("165.232.76.174", 8888)

server_ip = sys.argv[1]
serverPort = int(sys.argv[2])
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

    def good_packet(packet: bytes):
        return b"\n\n" in packet and Tools.PATTERN.fullmatch(packet.decode())
    
    def recv():
        temp = udp_sock.recv(2048)
        if Tools.good_packet(temp):
            command, headers, payload = Tools.packet_splitter(temp)
            # TODO: handle payload here
        else:
            return ""
        logging.info("Receive; {}; {}; {}".format(command, *headers))
        return (command, *headers)

    def packet_splitter(packet: bytes):
        packet = packet.decode()
        splited_packet = packet.split("\n")
        command = splited_packet[0]
        headers = splited_packet[1:packet.find("\n\n")-2]
        payload = splited_packet[packet.find("\n\n")-2:]
        return (command, headers, payload)
    
    def get_next_job():
        while True:
            try:
                jobs.get_nowait()() # run the job
            except queue.Empty:
                break

class Sender:


    def __init__(self, sock: socket.socket) -> None:
        self.socket = sock
        self.send_buff = bytearray()
        self.state = CLOSED
        self.send_syn() # make connection as soon as object is initialized

    def send_syn(self):
        h1 = "Sequence: 0"
        h2 = "Length: 0"
        packet = PACKET.format(comm=SYN, h1=h1, h2=h2).encode()
        Tools.send(packet, ("SYN", h1, h2))
        self.state = SYNC
        

    def write_in_buff(self, message: str):
        self.send_buff = bytearray(message).ljust(1024, b'\x00')

    def rcv_ack(self, message: tuple):
        #TODO: extract stuff from ack
        pass

    def send_from_buff(self):
        if len(self.send_buff) == 0:
            return
        bytes_sent = Tools.send(self.send_buff, ECHO_SERVER)
        self.send_buff = self.send_buff[bytes_sent:]

    def getstate(self):
        return self.state
    
    def timeout():
        pass


class Reciver:
    def __init__(self, sock: socket.socket) -> None:
        self.socket = sock
        self.rcv_buff = []
        self.pattern = re.compile(r"(SYN|DAT|FIN)\n(([a-zA-Z]+: [-1|\d]+\n)*)\n")
        self.state = CLOSED
        self.ack_number = 0
    
    def send_ack(self):
        h1 = f"Acknowledgment: {self.ack_number}"
        h2 = "Length: 0"
        packet = PACKET.format(comm=ACK, h1=h1, h2=h2).encode()
        Tools.send(packet, ("ACK", h1, h2))
        self.state = OPEN

    def check_buffer(self):
        message = None
        if self.rcv_buff.strip(b"\x00").decode().endswith("\n\n"):
            message = self.rcv_buff.strip(b"\x00").decode().strip("\n")
        self.rcv_buff = bytearray(1024) # cleaning the buffer
        return message
    
    def getstate(self):
        return self.state
    

rdp_receiver = Reciver(udp_sock)
rdp_sender = Sender(udp_sock)


while True:
    #if rdp_sender.getstate() == CLOSED:
    #    rdp_sender.send_syn()
    readable, writable, exceptional = select.select([udp_sock], [udp_sock], [udp_sock], timeout)
    if udp_sock in readable:
        message = Tools.recv()
        #print("raw_message:", message)
        #if the message in rcv_buf is complete (detect a new line):
        if not message:
            logging.info("Bad Message")
            #rdp_sender.write_in_buff(b"RST")
        else:
            #extract the message from rcv_buf, and split the message into RDP packets
            if message[0] == "ACK":
                rdp_sender.rcv_ack(message)
            elif message[0] == "SYN":
                jobs.put(rdp_receiver.send_ack)
            elif message[0] == "DAT":
                rdp_receiver.rcv_data("done")
    
    if udp_sock in writable:
        Tools.get_next_job()

    if udp_sock not in readable and udp_sock not in writable:
        if rdp_sender.getstate() == CLOSED and rdp_receiver.getstate() == CLOSED:
            break
        rdp_sender.timeout()