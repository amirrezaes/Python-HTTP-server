Feature: 200 and 404

Scenario Outline: 200 on success
  Given a request file <filename>
  When I connect to the server
  And I type in the request
  And I read 4096 bytes
  And I close the connection
  Then the status code line should be "HTTP/1.0 200 OK"

  Examples:
    | filename                          |
    | single_request_close.txt          |
    | connection_case_insensitive_1.txt |
    | connection_case_insensitive_2.txt |
    | space_after_colon_optional.txt    |

Scenario Outline: 404 on file access failure
  Given a request file <filename>
  When I connect to the server
  And I type in the request
  And I read 4096 bytes
  And I close the connection
  Then the status code line should be "HTTP/1.0 404 Not Found"

  Examples:
    | filename                          |
    | requested_file_does_not_exist.txt |

Scenario Outline: CRLF line ending
  Given a request file <filename>
  When I connect to the server
  And I type in the request
  And I read 4096 bytes
  And I close the connection
  And I partition the response at the first double-CRLF
  Then the header section should use the CRLF line ending

  Examples:
    | filename                          |
    | single_request_close.txt          |
    | requested_file_does_not_exist.txt |

Scenario Outline: File content integrity
  Given a static file <static> and its request file <request>
  When I connect to the server
  And I type in the request
  And I read 4096 bytes
  And I close the connection
  And I partition the response at the first double-CRLF
  Then the response body should match file data exactly

  Examples:
  | static     | request                  |
  | small.html | single_request_close.txt |
