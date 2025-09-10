# TXG MCP Desktop Extension (TypeScript)

A fully type-safe, self-contained Desktop Extension (DXT) that provides secure access to TXG (10x Genomics) CLI tools through the Model Context Protocol (MCP). Built with TypeScript for maximum type safety and reliability, this extension enables LLMs to interact with genomics analysis workflows through natural language commands, directly executing TXG CLI commands without requiring additional servers.

## Features

- **TypeScript**: Fully type-safe implementation with strict TypeScript configuration
- **Strong Typing**: All interfaces, arguments, and return types are strongly typed
- **Direct CLI Integration**: Executes TXG commands directly without intermediate servers
- **Project Management**: Create, list, and update projects
- **Cell Ranger Analyses**: Run count, multi, and aggr analyses
- **File Management**: Upload/download FASTQ files and analysis results
- **Reference Management**: Manage custom references
- **Annotation Models**: Access cell annotation models
- **Security**: Command allowlisting and input sanitization for safe execution
- **Configurable**: Adjustable timeout and logging settings
- **Error Handling**: Custom error types with detailed error information

## Installation

### Prerequisites

1. **TXG CLI**: Ensure the TXG CLI is installed and accessible at `/usr/local/bin/txg` (or configure a custom path)
2. **Node.js**: Version 16.0.0 or higher
3. **Claude Desktop**: Version 0.10.0 or higher

### Quick Install

1. Build the extension:
```bash
cd dxt
npm install
./build.sh
```

2. Install in Claude Desktop:
   - Open Claude Desktop
   - Go to Settings > Extensions
   - Click "Install from file"
   - Select the generated `txg-mcp.mcpb` file

### Manual Setup

1. Install dependencies:
```bash
cd dxt
npm install
```

2. Configure the extension:
   - Open the configuration UI at `ui/config.html`
   - Set the TXG executable path
   - Optionally configure timeout and logging settings

3. Start the server (for testing):
```bash
npm start
```

## Configuration

The extension can be configured through environment variables or the UI:

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| TXG Executable | `TXG_EXECUTABLE` | `/usr/local/bin/txg` | Path to TXG CLI |
| Command Timeout | `COMMAND_TIMEOUT` | `120000` | Max execution time (ms) |
| Verbose Logging | `VERBOSE_LOGGING` | `false` | Enable debug logging |

## Available Tools

### Project Management
- `list_projects`: List all available projects
- `create_project`: Create a new project
- `update_project`: Update project details

### Cell Ranger Analyses
- `create_cellranger_count_analysis`: Create a count analysis
- `create_cellranger_multi_analysis`: Create a multi analysis
- `create_cellranger_aggr_analysis`: Create an aggregation analysis
- `list_analyses`: List analyses in a project
- `get_analysis_details`: Get analysis details
- `list_analysis_files`: List files in an analysis
- `download_analysis_files`: Download analysis results

### File Management
- `list_fastqs`: List FASTQ files in a project
- `upload_fastqs`: Upload FASTQ files
- `list_project_files`: List project files
- `upload_project_file`: Upload a file to a project
- `download_project_file`: Download a file from a project

### Reference Management
- `list_references`: List custom references
- `get_reference`: Get reference details
- `update_reference`: Update reference information
- `upload_reference`: Upload a custom reference

### Annotation
- `list_annotation_models`: List available cell annotation models

## Architecture

This extension is completely self-contained and works by:

1. **Direct CLI Execution**: The MCP server directly spawns TXG CLI processes
2. **Security Layer**: Commands are validated against an allowlist and arguments are sanitized
3. **Stdio Transport**: Communication via standard MCP stdio protocol
4. **Error Handling**: Comprehensive error handling with timeout protection

### Project Structure
```
dxt/
├── src/                # TypeScript source files
│   ├── server/
│   │   └── index.ts   # MCP server implementation
│   ├── types/
│   │   └── index.ts   # Type definitions and interfaces
│   └── ui/
│       └── config.html # Configuration UI
├── dist/              # Compiled JavaScript (generated)
├── manifest.json      # Extension manifest
├── package.json       # Dependencies and scripts
├── tsconfig.json      # TypeScript configuration
├── .eslintrc.json     # ESLint configuration
├── build.sh          # Build script
└── README.md         # This file
```

## Security

The extension implements multiple security layers:

1. **Command Allowlisting**: Only pre-approved TXG commands can be executed
2. **Input Sanitization**: All arguments are sanitized to prevent injection
3. **Timeout Protection**: Commands have configurable timeout limits
4. **No Network Dependencies**: Runs entirely locally without external servers

### Allowed Commands

The following TXG command prefixes are allowed:
- `analyses.*` - Analysis operations
- `annotation.models.*` - Annotation model operations
- `fastqs.*` - FASTQ file operations
- `files.*` - General file operations
- `projects.*` - Project management
- `references.*` - Reference management

## Development

### Building from Source

1. Clone the repository
2. Navigate to the `dxt` directory
3. Run `npm install` to install dependencies
4. Run `./build.sh` to create the `.mcpb` bundle

### Testing

Run the test suite:
```bash
# Set the TXG executable path
export TXG_EXECUTABLE="/usr/local/bin/txg"

# Run tests
npm test

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Debugging

Enable verbose logging to see detailed command execution:
```bash
export VERBOSE_LOGGING=true
npm start
```

## Troubleshooting

### TXG CLI Not Found
1. Verify TXG CLI is installed: `which txg`
2. Update the executable path in configuration
3. Ensure the path has proper permissions

### Command Timeouts
1. Increase the timeout in configuration (max 600000ms)
2. Check if TXG commands are hanging
3. Review verbose logs for details

### Permission Errors
1. Ensure TXG CLI has necessary permissions
2. Check file/directory permissions for uploads/downloads
3. Verify the extension has access to required paths

## Support

For issues and questions:
- GitHub Issues: [Your Repository URL]
- Email: support@txg.com

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description

## Changelog

### Version 2.0.0
- Complete TypeScript rewrite with strong typing
- Custom error types for better error handling
- Strict TypeScript configuration for maximum safety
- ESLint integration for code quality
- All type definitions exported for extensibility

### Version 1.0.0
- Initial release with self-contained architecture
- Direct TXG CLI execution without Flask server
- Full command allowlisting and sanitization
- Comprehensive error handling
- All 20 TXG tools supported