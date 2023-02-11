#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2029 Zhiming Huang
#


import select
import socket
import sys
import queue
import re
import os.path
import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s: %(message)s', datefmt='%a %b %d %H:%M:%S %Z %Y')
#constants
PATTERN = re.compile(r"(GET )+(/\S*)+( HTTP/(1.0|1.1))\s+(\S*: *\S*)+(\s{2,})")
PATTERN_HEADERLESS = re.compile(r"(GET )+(/\S*)+( HTTP/(1.0|1.1))+\s{2,}")
PATTERN_SPLIT = re.compile(r"\s\s")
RESPONSE_CODE = 0
RESPONSE_MESSAGE = 1
DIRECTORY = 2
HEADER = 4
REQUEST_MESSAGE = 4


def log_handle(s:socket.socket, message:tuple):
    if not s:
        return
    client = "{}:{}".format(*s.getsockname())
    req = message[REQUEST_MESSAGE].split("\n")[0].strip()
    res = message[RESPONSE_MESSAGE].strip()
    logging.info("{} {}; {}".format(client, req, res))


def generate_response(message: str) -> tuple:
    matched =PATTERN.fullmatch(message) or PATTERN_HEADERLESS.fullmatch(message)
    if matched:
        if len(matched.groups()) > 3: # means there was a header
            header: str = matched[HEADER]
        else:
            header = ""
        directory: str = matched[DIRECTORY].lstrip("/") # second group is the directory
        if os.path.isfile(directory):
            return (200 ,"HTTP/1.0 200 OK\r\n", directory, header, message)
        else:
            return (404,"HTTP/1.0 404 Not Found\r\n", "", header, message)
    else:
        return (400 ,"HTTP/1.0 400 Bad Request\r\n", "", "", message)


def handle_directory(client: socket.socket, directory: str) -> None:
    with open(directory, 'rb') as f:
        content = f.read()
        length = len(content)
    while length:
        try:
            client.sendall(content)
            length = 0
        except BlockingIOError:
            try:
                sent_size = client.send(content)
                length -= sent_size
                content = content[sent_size:]
            except BlockingIOError:
                pass
        except:
            return
        finally:
            if not client:
                return


def client_handle(client: socket.socket, header: str, response_code: int) -> None:
    if not client:
        return
    if "keep-alive" in header.lower() and response_code!=400:
        return
    inputs.remove(client)
    outputs.remove(client)
    client.close()


def handle_response(client: socket.socket, response_code: int, response_message:str, directory: str, header: str) -> None:
    message = (response_message + header + "\r\n" + (header and "\r\n")).encode()
    if not client:
        return
    client.send(message) # https response will be sent in all cases
    if response_code == 200:
        if directory == "/":
            pass
        else:
            handle_directory(client, directory)

server_ip = sys.argv[1]
serverPort = int(sys.argv[2])
# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)
# Bind the socket to the port
server_address = (server_ip, serverPort)
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

keep_alives = set()



timeout = 30

while inputs:
    readable, writable, exceptional = select.select(inputs,
                                                    outputs,
                                                    inputs,
                                                    timeout)

    # Handle inputs
    for s in readable:

        if s is server:
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
                # if not add the message to the request message for s
                request_message[s] =  request_message[s] + message1
                message: str = request_message[s]
                # check if the end of the requests:
                if not message.endswith('\n\n') and not message.endswith('\r\n'):
                    continue
                # if it is the end of request, process the request
                m = [i+"\n\n" for i in PATTERN_SPLIT.split(message) if i]
                if len(m) > 1:
                    for i in m:
                        response: str = generate_response(i)
                        message_queues[s].put(response)
                else:
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
                handle_response(s, *next_msg[:REQUEST_MESSAGE]) #anything but request message\
                log_handle(s, next_msg)
                client_handle(s, next_msg[3], next_msg[RESPONSE_CODE]) # third index is the header
                
                

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
    
    if not (readable or writable or exceptional):
        for i in inputs:
            if i not in readable and i not in writable and i not in exceptional and i!= server:
                inputs.remove(i)
                if i in outputs:
                    outputs.remove(i)
                if i in message_queues:
                    message_queues.pop(i)
                i.close()
