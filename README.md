# 10x Genomics MCP Server for Claude Desktop

10x Genomics Cloud MCP server for Claude Desktop.

## Deploy to Claude Desktop

1. Build (see Installation section below) or download .mcpb package from **Releases**.
2. Open Claude Desktop
3. Go to Settings > Extensions > Browse
4. Install the package
5. Configure your access token

## Installation

### Prerequisites

- Node.js 18+ (comes with Claude Desktop)
- Access to 10x Genomics Cloud platform
- Valid 10x Genomics access token

### Development Setup

```bash
# 1. Install dependencies
npm install

# 2. Build TypeScript
npm run build

# 3. Run tests
npm test

# 4. Download TXG Binaries (or manually create them in package/bin/<darwin|linux|windows>):
npm run download-bin

# 5. Create MCP bundle
npm run pack

# 6. Deploy
 # Open Claude Desktop
 # Go to Settings > Extensions > Browse
 # Install .mcpb file

# 7. Query server capabilities and update reference documentation
# note: this is not needed for functionality, just make sure to run it before submitting a PR (makes it easier to review changes to the mcp APIs)
npm run generate-capabilities

# 8. For complete release build (clean + build + test + capabilities + pack):
npm run release
```

#### Access Token Management

The server requires a 10x Genomics access token. There are several ways to provide it:

1. **Pass as argument** (saved for future use):

   ```bash
   npm run start YOUR_ACCESS_TOKEN
   ```

2. **Use saved token** (from credentials.txt):
   ```bash
   npm run start
   ```

The token is automatically saved to `credentials.txt` (gitignored) when provided as an argument.

## Project Structure

```
  txg-mcp/
  ├── src/                   # TypeScript source code for MCP server
  ├── tests/                 # Test files
  ├── build/                 # Compiled JavaScript and binaries (content of the mcpb file)
  │   ├── server/            # Compiled server code
  │   ├── bin/               # Platform-specific TXG binaries
  │   └── node_modules/      # mcpb node dependencies
  ├── assets/                # Static assets
  ├── reference/             # Reference capabilities
  ├── scripts/               # Build and utility scripts
  ├── package.json           # NPM package configuration
  ├── manifest.json          # Claude Desktop extension manifest
  ├── tasks.sh               # Task for build, package, test, ..etc script
  ├── txg-node.mcpb          # MCP bundle file (output of npm run pack) - not this can be renamed to .zip to examine it's content
  └── credentials.txt        # Your access token (gitignored)
```

## Features

- **25+ Tools** for managing Cell Ranger analyses, projects, files, and references
- **Smart parameter confirmation** via MCP prompts
- **Async/await** throughout for non-blocking operations
- **Zod validation** for type-safe parameter handling
- **Structured error handling** with detailed responses

## How It Works

1. Claude Desktop starts the Node.js server via `node server/index.js`
2. Server communicates via stdio using MCP protocol (JSON-RPC 2.0)
3. Tools translate Claude's requests to TXG CLI commands
4. TXG CLI talk to Cloud Analysis APIs
5. Responses are formatted and returned to Claude

## Claude Desktop Extension Documentation

- **Documentation**: [Anthropic Desktop Extensions Documentation](https://www.anthropic.com/engineering/desktop-extensions)
- **MCP Protocol**: [Model Context Protocol Specification](https://modelcontextprotocol.io/)
