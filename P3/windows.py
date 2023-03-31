import socket
import struct

# Define constants
PACKET_SIZE = 1024
WINDOW_SIZE = 5
TIMEOUT = 1

# Create socket and bind to port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('localhost', 12345))

# Define packet structure
packet_struct = struct.Struct('I{}s'.format(PACKET_SIZE - 4))

# Initialize variables
expected_seq_num = 0
window_base = 0
window_packets = []
ack_received = False

while True:
    # Receive packet from sender
    data, addr = sock.recvfrom(PACKET_SIZE)
    seq_num, payload = packet_struct.unpack(data)

    # Check if packet is in order and within window size
    if seq_num == expected_seq_num and len(window_packets) < WINDOW_SIZE:
        # Add packet to window and send ACK to sender
        window_packets.append(payload)
        ack_packet = struct.pack('I', expected_seq_num)
        sock.sendto(ack_packet, addr)

        # Update variables for next expected sequence number and window base
        expected_seq_num += 1

        while len(window_packets) > 0 and window_packets[0] is not None:
            # Write received packets to file in order and slide window forward
            with open('received_file.txt', 'ab') as f:
                f.write(window_packets.pop(0))
            window_base += 1

    elif seq_num >= window_base and seq_num < (window_base + WINDOW_SIZE):
        # Packet is out of order but within window size, add to correct position in window list
        index = seq_num - window_base
        if index < len(window_packets):
            window_packets[index] = payload

        # Send ACK for last in-order packet received
        ack_packet = struct.pack('I', expected_seq_num - 1)
        sock.sendto(ack_packet, addr)

    # Handle packet loss by resending ACK for last in-order packet received
    if not ack_received:
        sock.settimeout(TIMEOUT)
        try:
            data, addr = sock.recvfrom(PACKET_SIZE)
            seq_num, payload = packet_struct.unpack(data)
            if seq_num == expected_seq_num - 1:
                ack_received = True
        except socket.timeout:
            ack_packet = struct.pack('I', expected_seq_num - 1)
            sock.sendto(ack_packet, addr)
    else:
        ack_received = False