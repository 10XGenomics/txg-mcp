#!/usr/bin/env python3
"""
Math Hello World MCP Server
A simple MCP server that adds two numbers together.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp.server import NotificationOptions
import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions

logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") == "true" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger("math-hello-world")

server = Server("math-hello-world")

@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools."""
    logger.debug("Listing available tools")
    return [
        types.Tool(
            name="add",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number to add"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number to add"
                    }
                },
                "required": ["a", "b"],
                "additionalProperties": False
            }
        )
    ]

@server.call_tool()
async def call_tool(
    name: str, 
    arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls."""
    logger.debug(f"Tool called: {name} with arguments: {arguments}")
    
    if name == "add":
        try:
            a = float(arguments.get("a", 0))
            b = float(arguments.get("b", 0))
            result = a + b
            
            logger.info(f"Addition: {a} + {b} = {result}")
            
            response = {
                "operation": "addition",
                "inputs": {"a": a, "b": b},
                "result": result,
                "message": f"The sum of {a} and {b} is {result}"
            }
            
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(response, indent=2)
                )
            ]
            
        except (TypeError, ValueError) as e:
            error_msg = f"Invalid input: {str(e)}"
            logger.error(error_msg)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": error_msg,
                        "inputs": arguments
                    }, indent=2)
                )
            ]
        except Exception as e:
            error_msg = f"Unexpected error during addition: {str(e)}"
            logger.error(error_msg)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": error_msg
                    }, indent=2)
                )
            ]
    
    error_msg = f"Unknown tool: {name}"
    logger.warning(error_msg)
    return [
        types.TextContent(
            type="text",
            text=json.dumps({
                "error": error_msg,
                "available_tools": ["add"]
            }, indent=2)
        )
    ]

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Math Hello World MCP Server")
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Server transport initialized")
            
            initialization_options = InitializationOptions(
                server_name="math-hello-world",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(
                        tools_changed=False,
                        prompts_changed=False,
                        resources_changed=False
                ),
                    experimental_capabilities={}
                )
            )
            
            await server.run(
                read_stream,
                write_stream,
                initialization_options
            )
            
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)