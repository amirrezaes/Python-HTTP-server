import time
from behave import when


def _send_line(s, line):
    n = s.send(line)
    if n != len(line):
        raise RuntimeError('Could not send the entire line in one packet')
    time.sleep(0.5)


@when('I run the partial line test')
def send_partial_lines(context):
    s = context.connection_sock
    _send_line(s, b'GET /small')
    _send_line(s, b'.html HTTP/1.0\n')
    _send_line(s, b'\n')


@when('I run the multiple line test')
def send_multiple_lines(context):
    s = context.connection_sock
    _send_line(s, b'GET /small.html HTTP/1.0\nConnection: keep-alive\n')
    _send_line(s, b'\n')
