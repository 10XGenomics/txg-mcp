#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Parse command line arguments
parser = argparse.ArgumentParser(description="10x Genomics MCP Server")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
args = parser.parse_args()

# Initialize server
mcp = FastMCP("10x-genomics")


# Main execution
if __name__ == "__main__":
    # Debug output if enabled
    if args.debug:
        print("Starting 10x Genomics MCP Server...", file=sys.stderr)

    # Run the server
    mcp.run()