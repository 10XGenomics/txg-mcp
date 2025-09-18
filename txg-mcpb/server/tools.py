#!/usr/bin/env python3

from txg_cli_manager import txg_cli
from middleware import to_response

def register_tools(mcp):
    """Register all 10x Genomics tools with the MCP server"""
    
    @mcp.tool(name="get_tool_version", description="Get the version of the TXG CLI tool.")
    async def get_tool_version() -> dict:
        return to_response(txg_cli.run_command(["--version"]))

    @mcp.tool(name="verify_auth", description="Verify authentication for the TXG CLI tool. Returns email of the authenticated user")
    async def verify_auth() -> dict:
        return to_response(txg_cli.run_command(["auth", "verify"]))
    
    # Add more tools here as you expand
    @mcp.tool(name="list_projects", description="List available projects")
    async def list_projects() -> dict:
        return to_response(txg_cli.run_command(["projects", "list"]))
    
    