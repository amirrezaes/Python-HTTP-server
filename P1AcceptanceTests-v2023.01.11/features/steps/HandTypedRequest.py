import logging
import time
from behave import given, when, then


logger = logging.getLogger(__name__)


@given('a request file {filename}')
def read_request_file(context, filename):
    _read_request_file(context, filename)


def _read_request_file(context, filename):
    endl_option = context.config.userdata.get('endl', 'lf')
    endl = b'\n'
    assert endl_option in ('crlf', 'lf')
    if endl_option == 'crlf':
        endl = b'\r\n'
    with open('requests/' + filename, 'rb') as f:
        context.lines = [s.rstrip() + endl for s in f.readlines()]


@given('a static file {static} and its request file {request}')
def read_static_file_and_request_file(context, static, request):
    with open('static/' + static, 'rb') as fs:
        context.expected_response_body = fs.read()
    _read_request_file(context, request)


@when('I type in the request')
def type_in_request(context):
    for line in context.lines:
        _send_line(context, line)


def _send_line(context, line):
    logger.info('> %r', line)
    time.sleep(0.1 * len(line))
    n = context.connection_sock.send(line)
    if n != len(line):
        raise RuntimeError('Could not fit the entire line into one packet')
    time.sleep(0.25)


@then('the status code line should be "{status_line}"')
def check_200_response(context, status_line):
    status_line_bin = status_line.encode('ascii')
    response = context.connection_response
    if not response.startswith(status_line_bin + b'\r\n') and \
       not response.startswith(status_line_bin + b'\n'):
        logger.error('Was looking for %r', status_line_bin)
        logger.error('Received %r...', response[0:32])
        raise AssertionError('Unexpected status code (see log)')


@given('a bad request file {bad}')
def read_bad_request_file(context, bad):
    context.bad_line_index = -1
    with open('bad_requests/' + bad, 'rb') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if lines[i].startswith(b'*'):
            context.bad_line_index = i
            lines[i] = lines[i][1:]
            break
    context.bad_request_lines = lines


@when('I type in the bad request line by line')
def type_in_bad_request_line_by_line(context):
    assert context.bad_line_index >= 0
    for i in range(0, context.bad_line_index):
        _send_line(context, context.bad_request_lines[i])

    start = context.bad_line_index
    end = len(context.bad_request_lines)
    context.actual_bad_line_index = -1
    for i in range(start, end):
        try:
            _send_line(context, context.bad_request_lines[i])
        except OSError:
            context.actual_bad_line_index = i
            break


@when('I partition the response at the first double-CRLF')
def partition_response(context):
    headers, delim, body = context.connection_response.partition(b'\r\n\r\n')
    if not delim:
        raise AssertionError('The response does not contain \\r\\n\\r\\n')
    context.response_headers = headers
    context.response_body = body


@then('the header section should use the CRLF line ending')
def check_header_crlf(context):
    for line in context.response_headers.split(b'\r\n'):
        if b'\n' in line:
            raise AssertionError('Bad line ending', line)


@then('the response body should match file data exactly')
def check_extra_lines(context):
    expected = context.expected_response_body
    actual = context.response_body
    index = actual.find(expected)
    if index == -1:
        logger.info('Expected: %r', expected)
        logger.info('Actual: %r', actual)
        raise AssertionError('The response body should contain file data')
    if index != 0:
        logger.info('Actual response body started with %r...', actual[0:8])
        raise AssertionError('The response body should start with file data')
    if len(actual) > len(expected):
        start = len(expected)
        end = start + 8
        logger.info('Garbage detected: %r...', actual[start:end])
        raise AssertionError('The response body was followed by garbage')
    assert expected == actual
