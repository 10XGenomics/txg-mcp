"""Tests for MCP protocol compliance."""

import json
import pytest
import subprocess
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "package"))
sys.path.insert(0, str(Path(__file__).parent.parent / "package" / "server"))

class TestMCPProtocol:
    """Test MCP protocol implementation."""

    @pytest.fixture
    def server_process(self, tmp_path, monkeypatch):
        """Start an MCP server subprocess for testing."""
        # Set required environment variables
        env = os.environ.copy()
        env['ACCESS_TOKEN'] = 'test_token'
        env['PYTHONPATH'] = str(Path(__file__).parent.parent / "package" / "lib")

        # Start server process
        server_path = Path(__file__).parent.parent / "package" / "server" / "main.py"
        process = subprocess.Popen(
            ['python3', str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(Path(__file__).parent.parent / "package")
        )

        yield process

        # Cleanup
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def send_request(self, process, method, params=None, id=1):
        """Send JSON-RPC request to the server."""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": id
        }
        if params is not None:
            request["params"] = params

        request_str = json.dumps(request) + "\n"
        process.stdin.write(request_str)
        process.stdin.flush()

        response_str = process.stdout.readline()
        return json.loads(response_str)

    def test_initialize_handshake(self, server_process):
        """Test the MCP initialization handshake."""
        # Send initialize request
        response = self.send_request(
            server_process,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )

        # Verify response structure
        assert "result" in response
        assert "serverInfo" in response["result"]
        assert response["result"]["serverInfo"]["name"] == "10x-genomics"
        assert "protocolVersion" in response["result"]
        assert "capabilities" in response["result"]

    def test_initialized_notification(self, server_process):
        """Test that server accepts initialized notification."""
        # First initialize
        self.send_request(
            server_process,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )

        # Send initialized notification (no response expected)
        server_process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        server_process.stdin.flush()

        # Server should be ready for next request
        # Test by sending tools/list
        response = self.send_request(server_process, "tools/list", None, 2)
        assert "result" in response
        assert "tools" in response["result"]

    def test_tools_list(self, server_process):
        """Test tools/list returns expected tools."""
        # Initialize first
        self.send_request(
            server_process,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )

        # Send initialized
        server_process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        server_process.stdin.flush()

        # Get tools list
        response = self.send_request(server_process, "tools/list", None, 2)

        assert "result" in response
        assert "tools" in response["result"]
        tools = response["result"]["tools"]

        # Verify some expected tools exist
        tool_names = [tool["name"] for tool in tools]
        assert "verify_auth" in tool_names
        assert "create_cellranger_count_analysis" in tool_names
        assert "list_projects" in tool_names
        assert "get_tool_version" in tool_names

        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_prompts_list(self, server_process):
        """Test prompts/list returns expected prompts."""
        # Initialize first
        self.send_request(
            server_process,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )

        # Send initialized
        server_process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        server_process.stdin.flush()

        # Get prompts list
        response = self.send_request(server_process, "prompts/list", None, 2)

        assert "result" in response
        assert "prompts" in response["result"]
        prompts = response["result"]["prompts"]

        # Verify our confirm_analysis_parameters prompt exists
        prompt_names = [prompt["name"] for prompt in prompts]
        assert "confirm_analysis_parameters" in prompt_names

        # Verify prompt structure
        for prompt in prompts:
            assert "name" in prompt
            assert "description" in prompt

    def test_invalid_method(self, server_process):
        """Test that server handles invalid methods correctly."""
        # Initialize first
        self.send_request(
            server_process,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )

        # Send invalid method
        response = self.send_request(server_process, "invalid/method", None, 2)

        # Should return error
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]