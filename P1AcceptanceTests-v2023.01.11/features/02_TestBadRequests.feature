Feature: Bad requests

Scenario Outline: Bad requests
  Given a bad request file <bad>
  When I connect to the server
  And I type in the bad request line by line
  And I read 4096 bytes
  And I test connectivity
  And I close the connection
  Then the connectivity test should fail
  And the status code line should be "HTTP/1.0 400 Bad Request"

  Examples:
    | bad                               |
    | all_lower_case_request_method.txt |
    | jumbled_first_line.txt            |
    | missing_colon.txt                 |
