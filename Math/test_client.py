#!/usr/bin/env python3
"""
MCP Client Test for Math Hello World Server
Tests the server with actual MCP protocol communication.
"""

import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_math_server():
    """Test the Math MCP server with real protocol communication."""
    
    # Server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["server/main.py"],
        env={"DEBUG": "true"}
    )
    
    print("Math MCP Server Test Client")
    print("=" * 50)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                print("\n1. Initializing connection...")
                await session.initialize()
                print("   ✓ Connected to server")
                
                # List available tools
                print("\n2. Listing available tools...")
                tools = await session.list_tools()
                print(f"   ✓ Found {len(tools.tools)} tool(s):")
                for tool in tools.tools:
                    print(f"      - {tool.name}: {tool.description}")
                
                # Test the add tool
                print("\n3. Testing 'add' tool...")
                test_cases = [
                    {"a": 5, "b": 3, "expected": 8},
                    {"a": 3.14, "b": 2.86, "expected": 6.0},
                    {"a": -5, "b": 3, "expected": -2},
                    {"a": 0, "b": 42, "expected": 42}
                ]
                
                for test in test_cases:
                    print(f"\n   Test: {test['a']} + {test['b']}")
                    result = await session.call_tool(
                        "add",
                        arguments={"a": test["a"], "b": test["b"]}
                    )
                    
                    # Parse the result
                    if result.content and len(result.content) > 0:
                        response = json.loads(result.content[0].text)
                        actual_result = response.get("result")
                        
                        if actual_result == test["expected"]:
                            print(f"   ✓ PASS: {actual_result}")
                        else:
                            print(f"   ✗ FAIL: Got {actual_result}, expected {test['expected']}")
                        
                        # Show full response
                        print(f"   Response: {response.get('message')}")
                
                # Test error handling
                print("\n4. Testing error handling...")
                
                print("   Testing invalid tool...")
                try:
                    await session.call_tool("invalid_tool", arguments={})
                    print("   ✗ Should have received an error")
                except Exception as e:
                    print(f"   ✓ Correctly handled: {e}")
                
                print("\n" + "=" * 50)
                print("✓ All tests completed successfully!")
                
    except FileNotFoundError:
        print("✗ Error: server/main.py not found")
        print("  Make sure you're running this from the Math directory")
        sys.exit(1)
    except ImportError:
        print("✗ Error: MCP library not installed")
        print("  Run: pip install mcp")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting MCP client test...")
    print("This will launch the server as a subprocess and communicate via stdio")
    print("")
    
    try:
        asyncio.run(test_math_server())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)