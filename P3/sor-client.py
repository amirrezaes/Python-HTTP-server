import socket
import struct
import sys
# Define packet size and sequence number range
PACKET_SIZE = 1024 * 2
SEQ_NUM_RANGE = 2**32
if len(sys.argv) > 7:
    files = sys.argv[5:7]
    server, port, buffer, payload_len = sys.argv[1:5]
    read_file, write_file = files[:len(files)// 2 + 1], files[len(files)//2 - 1:]
    print(read_file, write_file)
    input()
else:
    server, port, buffer, payload_len, read_file, write_file = sys.argv[1:]
    read_file = [read_file]
    write_file = [write_file]

# Create UDP socket and bind to port number
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.bind()



# Initialize expected sequence number and last ACK sent 
expected_seq_num = 0
last_ack_sent = 0

address = None
for file_index in range(len(read_file)):
    init_pack = struct.pack('!15sI', b"SYN|DAT|ACK", 0) + read_file.encode() + b"\n\n"
    sock.sendto(init_pack, (server, int(port)))
    address = None
    with open(read_file[file_index], "wb") as f:
        while True:
            # Receive packet from sender
            sock.settimeout(1)
            try:
                packet, address = sock.recvfrom(PACKET_SIZE)
                #print(packet)

                # Extract sequence number and data from packet
                flw_cntrl , seq_num = struct.unpack('!3sI', packet[:7])
                if flw_cntrl == b"FIN":
                    ack_packet = struct.pack('!15sI', b"ACK",expected_seq_num)
                    break
                elif flw_cntrl == b"SYN":
                    expected_seq_num += 1
                    last_ack_sent = expected_seq_num - 1
                    continue
                elif flw_cntrl == b"DAT":
                    data = packet[7:]
                    # Check if packet is in order
                    print(f"expected: {expected_seq_num}, got: {seq_num}")
                    if seq_num == expected_seq_num:
                        # Send ACK to sender with expected sequence number
                        ack_packet = struct.pack('!15sI', b"ACK",expected_seq_num)
                        sock.sendto(ack_packet, address)

                        # Process data received from sender
                        
                        f.write(data)
                        # Update expected sequence number and last ACK sent 
                        expected_seq_num += len(data)
                        last_ack_sent = expected_seq_num - (len(data) or 1)

                    else:
                        # Send ACK to sender with last ACK sent 
                        ack_packet = struct.pack('!15sI', b"ACK", last_ack_sent)
                        sock.sendto(ack_packet, address)
            except socket.timeout:
                    print("timeout")
                    ack_packet = struct.pack('!15sI', b"ACK", expected_seq_num)
                    sock.sendto(ack_packet, address)
                    print("sent ack", last_ack_sent)