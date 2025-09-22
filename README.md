# 10x Genomics Cloud Analysis Extension for Claude Desktop

A one-click MCP (Model Context Protocol) server extension that seamlessly integrates 10x Genomics Cloud Analysis platform with Claude Desktop, enabling natural language interaction with powerful single-cell and spatial genomics workflows.

## Key Features

### Analysis Pipeline Management
- **Cell Ranger Count**: Create single-cell RNA-seq analysis pipelines
- **Cell Ranger Multi**: Launch multi-sample and multi-library analyses
- **Cell Ranger Aggr**: Aggregate multiple Cell Ranger runs
- **Pipeline Monitoring**: Track analysis status and progress
- **Result Retrieval**: Download analysis outputs and reports

### Data Management
- **FASTQ File Management**: Upload, organize, and manage sequencing data
- **Project Organization**: Create and manage analysis projects
- **File Operations**: Upload/download files and analysis results
- **Library Configuration**: Set library types for FASTQ files

### Reference Genome Tools
- **Custom References**: Upload and manage custom reference genomes
- **Reference Metadata**: Update reference names and descriptions
- **Organism Support**: Multi-organism reference management

### Authentication & Access
- **Secure Authentication**: Token-based access to 10x Genomics Cloud
- **User Verification**: Validate authentication status

## Installation

### Prerequisites
- Claude Desktop application
- Python 3.10 or higher (required by MCP framework)
- Access to 10x Genomics Cloud Analysis platform
- Valid 10x Genomics access token

### Quick Install
1. Download the latest `.mcpb` bundle from the releases page
2. Open Claude Desktop
3. Go to Settings > Extensions
4. Install the downloaded extension file
5. Configure your 10x Genomics access token

## Usage Examples

Once installed, you can interact with 10x Genomics Cloud directly through Claude:

```
"Create a new Cell Ranger count analysis called 'PBMC_experiment' using the GRCh38 transcriptome"

"Upload my FASTQ files from /data/samples/ to the cancer_study project"

"Check the status of analysis abc123 and download the results when complete"

"List all my projects and show me the analyses in the immune_cells project"

"Create a new project called 'spatial_analysis' for my Visium experiments"
```

## Available Tools

The extension provides 25 comprehensive tools organized into categories. see `reference/mcp_capabilities_reference.json` for a detailed list.

## Development

### Setup Development Environment

1. Install dependencies:
```bash
./tasks.sh install-requirements
```

2. Download TXG CLI binaries (or manually create them in package/bin/<darwin|linux|windows>):
```bash
./tasks.sh download-bin
```

3. Create the MCP bundle:
```bash
./tasks.sh pack
```
The packaged `.mcpb` file will be created in the `build/` directory.

4. Install the extension
- Open Claude Desktop
- Go to Settings > Extensions
- Install the downloaded extension file

### Development Tasks Script

The `tasks.sh` script provides common development operations. run it to see detailed help.

### Project Structure

```
txg-mcp/
|-- package/
|   |-- manifest.json            # Extension metadata and configuration
|   |-- requirements.txt         # Python dependencies
|   |-- icon.png                 # Extension icon
|   |-- server/                  # Server source code
|   |-- bin/                     # TXG CLI binaries (darwin/linux/windows)
|   `-- lib/                     # Python dependencies
|-- scripts/                     # Various scripts for development
|-- build/                       # output mcp bundle
|-- reference/                   # Reference spec for the server
|-- tests/                       # Tests
|-- tasks.sh                     # Development tasks script
`-- README.md                    # This file
```

### Testing

```bash
# Run all tests
./tasks.sh run-tests

# Run specific test categories
./tasks.sh run-tests unit         # Unit tests only
./tasks.sh run-tests integration  # Integration tests only
./tasks.sh run-tests coverage     # Generate coverage report
./tasks.sh run-tests quick        # Quick smoke tests
./tasks.sh run-tests protocol     # MCP protocol compliance tests
```

```bash
# Run the server locally to test APIs manually.
./tasks.sh run-server YOUR_ACCESS_TOKEN
```

```bash
# Query server capabilities and update reference documentation
./tasks.sh generate-capabilities
```

### Claude Desktop Extensions Documentation
- **Documentation**: [Anthropic Desktop Extensions Documentation](https://www.anthropic.com/engineering/desktop-extensions)
- **MCP Protocol**: [Model Context Protocol Specification](https://modelcontextprotocol.io/)