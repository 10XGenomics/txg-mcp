#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import asyncio
from txg_cli_manager import txg_cli

# Parse command line arguments
parser = argparse.ArgumentParser(description="10x Genomics MCP Server")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
args = parser.parse_args()

# Initialize server
mcp = FastMCP("10x-genomics")

@mcp.tool(name="get_tool_version", description="Get the version of the TXG CLI tool.")
async def get_tool_version() -> dict:
    """
    Get the version of the 10x Genomics tools.
    
    Returns:
        A dictionary containing version information for various 10x tools.
    """
    
    stdout_log, stderr_log, returncode = txg_cli.run_command(["--version"])
    
    return {
        "content": stdout_log,
        "stderr": stderr_log,
        "returncode": returncode,
        "success": returncode == 0
    }
    
# Main execution
if __name__ == "__main__":
    # Debug output if enabled
    if args.debug:
        print("Starting 10x Genomics MCP Server...", file=sys.stderr)

    # Run the server
    asyncio.run(mcp.run())