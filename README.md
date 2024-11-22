# Python HTTP Server

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A robust HTTP server implementation with support for multiple clients and concurrent connections, developed as part of CSC361 (Computer Communications & Networks) at the University of Victoria.

## Project Components

### 1. HTTP Client/Server
- Multi-client support with concurrent connection handling
- Connection header implementation
- Response codes: 200 (OK), 400 (Bad Request), 404 (Not Found)
- Thread-safe request processing

### 2. Reliable Data Protocol (RDP)
- Custom implementation of reliable data transfer over UDP
- Flow control mechanisms
- Acknowledgment (ACK) system
- Handles network unreliability and packet loss
- Congestion control implementation

### 3. HTTP over RDP
- Integration of HTTP protocol with RDP layer
- Reliable web data transfer over unreliable connections
- Maintains HTTP semantics while using custom transport protocol

## Technical Features

- **Concurrent Processing**: Handle multiple client requests simultaneously
- **Thread Safety**: Proper synchronization for shared resources
- **Protocol Implementation**: Custom network protocol stack
- **Error Handling**: Robust error detection and recovery
- **Performance Optimization**: Efficient resource utilization

## Architecture

```plaintext
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ HTTP Client │ ←→  │ RDP Protocol │ ←→  │ UDP Network │
└─────────────┘     └──────────────┘     └─────────────┘
```

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/amirrezaes/Python-HTTP-server.git
cd Python-HTTP-server
```

2. Run the server:
```bash
python3 server.py
```

3. Connect with a client:
```bash
python3 client.py
```

## Project Structure

```
.
├── P1/                 # HTTP Client/Server Implementation
├── P2/                 # RDP Protocol Implementation
├── P3/                 # HTTP over RDP Integration
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- University of Victoria CSC361 course staff
- Network protocol design principles
- TCP/IP protocol suite documentation
