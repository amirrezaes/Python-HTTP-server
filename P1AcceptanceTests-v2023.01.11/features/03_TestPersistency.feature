Feature: Persistency

Scenario Outline: Connection header
  Given a request file <filename>
  When I connect to the server
  And I type in the request
  And I read 4096 bytes
  And I test connectivity
  And I close the connection
  Then the connectivity test should <pass_or_fail>

  Examples:
    | filename                        | pass_or_fail |
    | single_request_close.txt        | fail         |
    | no_connection_header_200.txt    | fail         |
    | no_connection_header_404.txt    | fail         |
    | keep_alive_requests_200_200.txt | pass         |
    | keep_alive_requests_404_200.txt | pass         |
    | keep_alive_and_then_close.txt   | fail         |
