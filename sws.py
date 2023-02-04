#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2029 Zhiming Huang
#


import select
import socket
import sys
import queue
import time
import re
import os.path

#constants
PATTERN = re.compile(r"(GET )+(/\S*)+( HTTP/1.0)\s+(\S*: *\S*)+(\s{2})")
PATTERN_HEADERLESS = re.compile(r"(GET )+(/\S*)+( HTTP/1.0)+\s{2}")
RESPONSE_CODE = 0
RESPONSE_MESSAGE = 1
DIRECTORY = 2
HEADER = 4


def handle_header():
    pass

def generate_response(message: str) -> tuple:
    matched =PATTERN.fullmatch(message) or PATTERN_HEADERLESS.fullmatch(message)
    if matched:
        if len(matched.groups()) > 3: # means there was a header
            header: str = matched[HEADER]
        else:
            header = ""
        directory: str = matched[DIRECTORY].lstrip("/") # second group is the directory
        if os.path.isfile(directory):
            return (200 ,"HTTP/1.0 200 OK\r\n", directory, header)
        else:
            return (404,"HTTP/1.0 404 Not Found\r\n", "", header)
    else:
        return (400 ,"HTTP/1.0 400 Bad Request\r\n", "", "")


def handle_directory(client: socket.socket, directory: str) -> None:
    with open(directory, 'rb') as f:
        client.send(f.read())


def client_handle(client: socket.socket, header: str):
    if "keep-alive" in header.lower():
        return
    inputs.remove(client)
    outputs.remove(client)
    client.close()


def handle_response(client: socket.socket, response_code: int, response_message:str, directory: str, header: str) -> None:
    message = (response_message + header + "\r\n" + (header and "\r\n")).encode()
    print("message being sent: ", message)
    client.send(message) # https response will be sent in all cases
    if response_code == 200:
        if directory == "/":
            pass
        else:
            handle_directory(client, directory)
    client_handle(client, header)

server_ip = sys.argv[1]
serverPort = int(sys.argv[2])
# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)
# Bind the socket to the port
server_address = (server_ip, serverPort)
#print('starting up on {} port {}'.format(*server_address),
#      file=sys.stderr)
server.bind(server_address)

# Listen for incoming connections
server.listen(5)

# Sockets from which we expect to read
inputs = [server]

# Sockets to which we expect to write
outputs = []

# Outgoing message queues (socket:Queue)
message_queues = {}

# request message
request_message = {}



timeout = 30

print("socket created, listening...")

while inputs:

    # Wait for at least one of the sockets to be
    # ready for processing
#    print('waiting for the next event', file=sys.stderr)
    readable, writable, exceptional = select.select(inputs,
                                                    outputs,
                                                    inputs,
                                                    timeout)

    # Handle inputs
    for s in readable:

        if s is server:
            print("new server")
            # A "readable" socket is ready to accept a connection
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)
            request_message[connection] = ""
            #new_request[s] = True
            #persistent_socket[connection] = True
            # Give the connection a queue for data
            # we want to send
            message_queues[connection] = queue.Queue()

        else:
            message1 =  s.recv(1024).decode()
            if message1:
                # First check if bad requests
                print("Recived data from", s.getpeername())
                # if not add the message to the request message for s
                request_message[s] =  request_message[s] + message1
                message: str = request_message[s]
                print("data start: ", message.encode(), "data end")
                # check if the end of the requests:
                if not message.endswith('\n\n'):
                    continue
                # if it is the end of request, process the request
                response: str = generate_response(message)
                message_queues[s].put(response)
                request_message[s] = "" # massage fuly retrived, clear the buffer
                # add the socket s to the output list for watching writability
                if s not in outputs:
                    outputs.append(s)

            else:
                pass
                # handle the situation where no messages received

    # Handle outputs
    for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
            # No messages need to be sent so stop watching
                outputs.remove(s)
                if s not in inputs:
                    s.close()
                    del message_queues[s]
                    del request_message[s]
            else:
                #print logs and send messages
                #print_log(s,message_request,printresponse)
                handle_response(s, *next_msg)
                
                

    # Handle "exceptional conditions"
    for s in exceptional:
        #print('exception condition on', s.getpeername(),
         #     file=sys.stderr)
        # Stop listening for input on the connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

        # Remove message queue
        del message_queues[s]
    
    if s not in readable and writable and exceptional:
        pass
        #handle timeout events


