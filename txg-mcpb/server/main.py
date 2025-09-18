#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import asyncio
from txg_cli_manager import CommandResult, txg_cli

# Parse command line arguments
parser = argparse.ArgumentParser(description="10x Genomics MCP Server")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
args = parser.parse_args()

# Initialize server
mcp = FastMCP("10x-genomics")

@mcp.tool(name="get_tool_version", description="Get the version of the TXG CLI tool.")
async def get_tool_version() -> dict:
    return to_response(txg_cli.run_command(["--version"]))

@mcp.tool(name="verify_auth", description="Verify authentication for the TXG CLI tool. Returns email of the authenticated user")
async def verify_auth() -> dict:
    return to_response(txg_cli.run_command(["auth", "verify"]))


def to_response(command_result: CommandResult) -> dict:
    """
    Convert raw command execution result tuple into formatted response dict.
    
    Args:
        command_result: Tuple of (stdout, stderr, returncode) from txg_cli.run_command()
        
    Returns:
        Dictionary with processed command results ready for client response
    """
    content, error, returncode, full_command = command_result
    
    # # Clean up output strings
    # cleaned_stdout = stdout.strip() if stdout else ""
    # cleaned_stderr = stderr.strip() if stderr else ""
    
    # TODO: Add filtering logic here later if needed
    # TODO: Add error code normalization if needed
    # TODO: Add logging/metrics if needed
    
    return {
        "content": content,
        "error": error,
        "returncode": returncode,
        "success": returncode == 0,
        "dbg-full-command": full_command  # TODO: Remove this debug field later
    }

# Main execution
if __name__ == "__main__":
    # Debug output if enabled
    if args.debug:
        print("Starting 10x Genomics MCP Server...", file=sys.stderr)

    # Run the server
    asyncio.run(mcp.run())