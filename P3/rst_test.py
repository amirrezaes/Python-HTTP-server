import socket
import sys
import datetime,time

def localtime():
    #localtime = time.asctime(time.localtime(time.time()))
    #return localtime
    localtime = time.strftime("%a %b %d %H:%M:%S %Z %Y", time.localtime())
    return localtime

#usage: python3 rst_test.py server_ip server_port

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
address = (server_ip,server_port)
try:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #Create the UDP socket
except socket.error:
    print("Failed to create socket\n")
    sys.exit()
clientSocket.settimeout(1)

rdppayload = '''GET /small.html HTTP/1.0

'''

datalen = len(rdppayload)

rdpheader = '''SYN|DAT|ACK|FIN
Sequence: 0
Length: '''+ str(datalen) + '''
Acknowledgement: -1
Windows: 5120

'''
rdppacket = rdpheader + rdppayload

while True:
    clientSocket.sendto(rdppacket.encode(),address)
    print(localtime()+ ": Send; SYN|DAT|ACK|FIN; Sequence: 0; Length: "+str(datalen)+"; Acknowledgment: -1; Window: 5120")
    try:
        reply,address = clientSocket.recvfrom(2048)
    except socket.timeout:
        continue
    else:
        if "RST" in reply.decode():
            print("RST Received")
        break
        

