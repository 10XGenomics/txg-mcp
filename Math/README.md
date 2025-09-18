# Math Hello World MCP Extension

A simple Desktop Extension (MCPB) that demonstrates MCP server implementation in Python. This extension provides a basic addition tool that adds two numbers together.

## Features

- **Simple Addition Tool**: Add two numbers and get a formatted JSON response
- **Error Handling**: Comprehensive error handling with informative messages
- **Debug Mode**: Configurable debug logging via manifest settings
- **Cross-Platform**: Works on macOS, Windows, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Install the required dependencies:
```bash
cd Math
pip install -r requirements.txt
```

2. Test the server locally:
```bash
python server/main.py
```

## Usage

Once installed in a compatible application (like Claude Desktop), the extension provides the following tool:

### Add Tool

Adds two numbers together and returns the result in JSON format.

**Parameters:**
- `a` (number, required): First number to add
- `b` (number, required): Second number to add

**Example Request:**
```json
{
  "tool": "add",
  "arguments": {
    "a": 5,
    "b": 3
  }
}
```

**Example Response:**
```json
{
  "operation": "addition",
  "inputs": {
    "a": 5,
    "b": 3
  },
  "result": 8,
  "message": "The sum of 5 and 3 is 8"
}
```

## Configuration

The extension supports the following configuration options in the manifest:

- **debug_mode** (boolean): Enable debug logging output (default: false)

## Development

### Project Structure
```
Math/
├── manifest.json       # MCPB manifest file
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── server/
    └── main.py        # MCP server implementation
```

### Testing Locally

To test the MCP server directly:

```bash
# Run the server
python server/main.py

# The server communicates via stdio, so you'll need an MCP client to interact with it
```

### Debugging

Enable debug mode by setting the environment variable:
```bash
DEBUG=true python server/main.py
```

## Error Handling

The server includes comprehensive error handling:
- Invalid input validation
- Type checking for numerical inputs  
- Graceful handling of unknown tools
- Detailed error messages in JSON format

## License

MIT

## Contributing

This is a simple demonstration extension. For production use, consider:
- Adding more mathematical operations
- Implementing input validation schemas
- Adding unit tests
- Enhancing error recovery mechanisms
- Adding performance monitoring