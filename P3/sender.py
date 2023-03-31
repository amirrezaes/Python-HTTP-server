import socket
import struct


# Define packet size and sequence number range
PACKET_SIZE = 1024
SEQ_NUM_RANGE = 2**32

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('localhost', 12345))

# Set receiver address and port number
receiver_address = ('localhost', 12345)


# Initialize sequence number and expected ACK number
seq_num = 0
expected_ack_num = 0

while True:
    # Read data from file or input stream
    file = input("Enter message to send: ")
    with open(file, 'rb') as f:
        while data:=f.read(1024):

        # Create packet with sequence number and data
            packet = struct.pack('!3sI', b"DAT", seq_num) + data

            # Send packet to receiver
            sock.sendto(packet, receiver_address)

            # Wait for ACK from receiver with timeout of 1 second
            sock.settimeout(1)
            try:
                ack_packet, address = sock.recvfrom(PACKET_SIZE)
                ack_num = struct.unpack('!3sI', ack_packet[:7])[1]
                if ack_num == expected_ack_num:
                    print("Packet", seq_num, "sent successfully")
                    seq_num += 1
                    expected_ack_num += 1
                else:
                    print("ACK", ack_num, "received out of order")
            except socket.timeout:
                print("Timeout waiting for ACK")
    fin_pack = struct.pack('!3sI', b"FIN", seq_num)
    sock.sendto(fin_pack, receiver_address)
