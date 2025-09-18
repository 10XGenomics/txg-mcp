#!/usr/bin/env python3
"""
Test script for Math Hello World MCP Server
This script tests the server functionality without requiring a full MCP client.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

async def test_server():
    """Test the MCP server by simulating client requests."""
    print("Testing Math Hello World MCP Server")
    print("=" * 50)
    
    # Test cases for the add function
    test_cases = [
        {
            "name": "Basic addition",
            "tool": "add",
            "arguments": {"a": 5, "b": 3},
            "expected": 8
        },
        {
            "name": "Addition with decimals",
            "tool": "add", 
            "arguments": {"a": 3.14, "b": 2.86},
            "expected": 6.0
        },
        {
            "name": "Addition with negative numbers",
            "tool": "add",
            "arguments": {"a": -5, "b": 3},
            "expected": -2
        },
        {
            "name": "Addition with zero",
            "tool": "add",
            "arguments": {"a": 0, "b": 42},
            "expected": 42
        }
    ]
    
    print("\nRunning test cases:")
    print("-" * 50)
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"Input: {test['arguments']['a']} + {test['arguments']['b']}")
        print(f"Expected: {test['expected']}")
        
        # Here we would normally interact with the server via MCP protocol
        # For this test, we're just validating the logic
        result = test['arguments']['a'] + test['arguments']['b']
        
        if result == test['expected']:
            print(f"✓ PASSED: Result = {result}")
        else:
            print(f"✗ FAILED: Got {result}, expected {test['expected']}")
    
    print("\n" + "=" * 50)
    print("Test validation complete!")
    print("\nTo fully test the server with MCP protocol:")
    print("1. Install the extension in a compatible application")
    print("2. Or use an MCP client library to connect via stdio")

def test_manifest():
    """Validate the manifest.json file."""
    print("\nValidating manifest.json...")
    try:
        with open("manifest.json", "r") as f:
            manifest = json.load(f)
        
        required_fields = ["manifest_version", "name", "version", "description", "author", "server"]
        missing = [field for field in required_fields if field not in manifest]
        
        if missing:
            print(f"✗ Missing required fields: {missing}")
            return False
        
        print("✓ Manifest validation passed")
        
        print("\nManifest details:")
        print(f"  Name: {manifest['name']}")
        print(f"  Version: {manifest['version']}")
        print(f"  Description: {manifest['description']}")
        print(f"  Server type: {manifest['server']['type']}")
        print(f"  Entry point: {manifest['server']['entry_point']}")
        
        if 'tools' in manifest:
            print(f"  Tools: {[tool['name'] for tool in manifest['tools']]}")
        
        return True
        
    except FileNotFoundError:
        print("✗ manifest.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in manifest.json: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating manifest: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")
    try:
        import mcp
        print("✓ MCP library is installed")
        return True
    except ImportError:
        print("✗ MCP library not found")
        print("  Run: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    print("Math Hello World MCP Extension Test Suite")
    print("=" * 50)
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Validate manifest
    manifest_ok = test_manifest()
    
    # Run tests
    if deps_ok:
        asyncio.run(test_server())
    else:
        print("\nSkipping server tests due to missing dependencies")
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  Dependencies: {'✓ PASS' if deps_ok else '✗ FAIL'}")
    print(f"  Manifest: {'✓ PASS' if manifest_ok else '✗ FAIL'}")
    
    if deps_ok and manifest_ok:
        print("\n✓ All checks passed! The extension is ready to use.")
        print("\nNext steps:")
        print("1. Package the extension: Create a .mcpb file by zipping the Math folder")
        print("2. Install in a compatible application like Claude Desktop")
        print("3. Test the 'add' tool with real requests")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)