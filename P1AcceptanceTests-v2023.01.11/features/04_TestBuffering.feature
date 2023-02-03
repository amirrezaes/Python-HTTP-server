Feature: Buffering

Scenario: Buffer partial lines
  When I connect to the server
  And I run the partial line test
  And I read 4096 bytes
  And I test connectivity
  And I close the connection
  Then the status code line should be "HTTP/1.0 200 OK"
  And the connectivity test should fail


Scenario: Read a multi-line recv buffer
  When I connect to the server
  And I run the multiple line test
  And I read 4096 bytes
  And I test connectivity
  And I close the connection
  Then the status code line should be "HTTP/1.0 200 OK"
  And the connectivity test should pass
