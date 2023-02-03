import logging
import select
import socket
import time
from behave import when, then


logger = logging.getLogger(__name__)


@when('I connect to the server')
def connect_to_server(context):
    addr = context.config.userdata.get('address', '127.0.0.1')
    port = int(context.config.userdata.get('port', '8080'))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Send data immediately
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((addr, port))
    context.connection_sock = sock


@when('I read {number} bytes')
def read_that_many_bytes(context, number):
    time.sleep(0.25)
    s = context.connection_sock
    rlist, _, elist = select.select([s], [], [s], 3)
    if not rlist and not elist:
        raise OSError('sock.recv timed out!')
    _append_to_response(context, s.recv(int(number)))


def _append_to_response(context, data):
    if not hasattr(context, 'connection_response'):
        context.connection_response = b''
    context.connection_response += data


@when('I close the connection')
def close_connection(context):
    try:
        context.connection_sock.close()
    except OSError:
        pass


@when('I test connectivity')
def check_connectivity(context):
    result = _connectivity_via_recv(context)
    context.connection_active = result


def _connectivity_via_recv(context):
    s = context.connection_sock
    while True:
        rlist, wlist, elist = select.select([s], [], [s], 0.5)
        if not rlist and not elist:
            # Receive buffer is empty and the connection is open
            return True
        if elist:
            logger.info('Connection not active')
            return False
        if rlist:
            try:
                data = s.recv(4096)
            except OSError as exc:
                # RST?
                logger.info('Connection not active: %r', exc)
                return False
            if not data:
                # Connection closed via the FIN packet
                logger.info('Connection not active: found EOF')
                return False
            else:
                # Read till the end of the recv buffer
                _append_to_response(context, data)
                continue


def _connectivity_via_send(context):
    sock = context.connection_sock
    try:
        # In order to detect RST we must call `send` at least 2 times
        _send_line_slowly(sock, b'GET /small.html HTTP/1.0\n')
        _send_line_slowly(sock, b'\n')
        return True
    except OSError as e:
        # Connection closed via the RST packet
        logger.info('Connection not active: %r', e)
        try:
            sock.close()
        except OSError:
            pass
        return False


def _send_line_slowly(sock, line):
    logger.info('Connectivity test: > %r', line)
    time.sleep(0.25)
    n = sock.send(line)
    if n != len(line):
        raise RuntimeError('Could not fit the entire line into one packet')


@then('the connectivity test should {expected_result}')
def expect_connectivity(context, expected_result):
    assert expected_result in ('pass', 'fail')
    assert context.connection_active in (True, False)
    assert context.connection_active == (expected_result == 'pass')
