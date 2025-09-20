#!/usr/bin/env python3
"""
Query MCP server capabilities via JSON-RPC protocol.

This script starts an MCP server as a subprocess and queries its capabilities
using the MCP JSON-RPC protocol over stdio. It retrieves tools, resources,
and prompts information and outputs them as a formatted JSON structure.

Usage:
    python query_mcp_capabilities.py <server_path> <lib_path> <access_token>
"""

import json
import sys
import subprocess
import os
from typing import Dict, Any, Optional


def send_jsonrpc(process: subprocess.Popen, method: str, params: Optional[Dict[str, Any]] = None, id: int = 1) -> Dict[str, Any]:
    """
    Send a JSON-RPC request to the process and return the response.

    Args:
        process: The subprocess running the MCP server
        method: The JSON-RPC method to call
        params: Optional parameters for the method
        id: The request ID

    Returns:
        The JSON-RPC response as a dictionary
    """
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "id": id
    }
    if params is not None:
        request["params"] = params

    # Send request
    request_str = json.dumps(request) + "\n"
    process.stdin.write(request_str)
    process.stdin.flush()

    # Read response
    response_str = process.stdout.readline()

    try:
        return json.loads(response_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {response_str}", file=sys.stderr)
        raise e


def query_capabilities(server_path: str, lib_path: str, access_token: str) -> Dict[str, Any]:
    """
    Query all capabilities from an MCP server.

    Args:
        server_path: Path to the MCP server Python script
        lib_path: Path to the Python libraries directory
        access_token: Access token for authentication

    Returns:
        Dictionary containing all server capabilities
    """
    # Start the server as a subprocess
    # Change to package directory to match how manifest.json expects it
    package_dir = os.path.dirname(os.path.dirname(server_path))  # Go up to package/
    server_relative = os.path.relpath(server_path, package_dir)  # Get server/main.py

    # Set up environment for the subprocess
    # lib_path should be relative to package_dir for proper imports
    lib_relative = os.path.relpath(lib_path, package_dir)
    env = os.environ.copy()
    env['PYTHONPATH'] = lib_relative
    env['ACCESS_TOKEN'] = access_token

    process = subprocess.Popen(
        ['python3', server_relative],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=package_dir
    )

    try:
        capabilities = {}

        # Step 1: Send initialize request
        init_response = send_jsonrpc(process, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-capabilities-generator",
                "version": "1.0.0"
            }
        }, 1)

        if "result" in init_response:
            capabilities["server_info"] = init_response["result"].get("serverInfo", {})
            capabilities["protocol_version"] = init_response["result"].get("protocolVersion", "")
            capabilities["capabilities"] = init_response["result"].get("capabilities", {})

        # Step 2: Send initialized notification (no response expected)
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        process.stdin.flush()

        # Step 3: Get tools list
        # Try with params=null (not omitted)
        try:
            # Send with explicit null params
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": None,
                "id": 2
            }
            process.stdin.write(json.dumps(tools_request) + "\n")
            process.stdin.flush()
            tools_response_str = process.stdout.readline()
            tools_response = json.loads(tools_response_str)

            if "result" in tools_response:
                capabilities["tools"] = tools_response["result"].get("tools", [])
            elif "error" in tools_response:
                capabilities["tools"] = []
                capabilities["tools_error"] = tools_response.get("error", "Unknown error")
        except Exception as e:
            capabilities["tools"] = []
            capabilities["tools_error"] = str(e)

        # Step 4: Get resources list
        # Try with params=null (not omitted)
        try:
            resources_request = {
                "jsonrpc": "2.0",
                "method": "resources/list",
                "params": None,
                "id": 3
            }
            process.stdin.write(json.dumps(resources_request) + "\n")
            process.stdin.flush()
            resources_response_str = process.stdout.readline()
            resources_response = json.loads(resources_response_str)

            if "result" in resources_response:
                capabilities["resources"] = resources_response["result"].get("resources", [])
            elif "error" in resources_response:
                capabilities["resources"] = []
                capabilities["resources_error"] = resources_response.get("error", "Unknown error")
        except Exception as e:
            capabilities["resources"] = []
            capabilities["resources_error"] = str(e)

        # Step 5: Get prompts list
        # Try with params=null (not omitted)
        try:
            prompts_request = {
                "jsonrpc": "2.0",
                "method": "prompts/list",
                "params": None,
                "id": 4
            }
            process.stdin.write(json.dumps(prompts_request) + "\n")
            process.stdin.flush()
            prompts_response_str = process.stdout.readline()
            prompts_response = json.loads(prompts_response_str)

            if "result" in prompts_response:
                capabilities["prompts"] = prompts_response["result"].get("prompts", [])
            elif "error" in prompts_response:
                capabilities["prompts"] = []
                capabilities["prompts_error"] = prompts_response.get("error", "Unknown error")
        except Exception as e:
            capabilities["prompts"] = []
            capabilities["prompts_error"] = str(e)

        return capabilities

    finally:
        # Terminate the server gracefully
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 4:
        print("Usage: python query_mcp_capabilities.py <server_path> <lib_path> <access_token>", file=sys.stderr)
        sys.exit(1)

    server_path = sys.argv[1]
    lib_path = sys.argv[2]
    access_token = sys.argv[3]

    # Validate paths
    if not os.path.exists(server_path):
        print(f"Error: Server script not found: {server_path}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(lib_path):
        print(f"Error: Library directory not found: {lib_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Query capabilities
        capabilities = query_capabilities(server_path, lib_path, access_token)

        # Output as formatted JSON
        print(json.dumps(capabilities, indent=2))

    except Exception as e:
        print(f"Error querying capabilities: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()