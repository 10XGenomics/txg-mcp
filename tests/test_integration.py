"""Integration tests for the MCP server."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.fixtures.mock_responses import *

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "package"))
sys.path.insert(0, str(Path(__file__).parent.parent / "package" / "server"))

class TestIntegration:
    """Test integrated workflows."""

    @pytest.fixture
    def mock_mcp_server(self):
        """Create a mock MCP server with tools registered."""
        from mcp.server.fastmcp import FastMCP
        from tools import register_tools
        from prompts import register_prompts

        mcp = FastMCP("test-server")
        register_tools(mcp)
        register_prompts(mcp)
        return mcp

    @pytest.mark.asyncio
    async def test_tools_are_registered(self, mock_mcp_server):
        """Test that all expected tools are registered."""
        tools = await mock_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        # Core tools
        assert "get_tool_version" in tool_names
        assert "verify_auth" in tool_names

        # Analysis tools
        assert "create_cellranger_multi_analysis" in tool_names
        assert "create_cellranger_count_analysis" in tool_names
        assert "create_cellranger_aggr_analysis" in tool_names
        assert "list_analyses" in tool_names
        assert "get_analysis_details" in tool_names

        # Project tools
        assert "list_projects" in tool_names
        assert "create_project" in tool_names
        assert "update_project" in tool_names

        # File management tools
        assert "upload_fastqs" in tool_names
        assert "list_fastqs" in tool_names
        assert "upload_project_file" in tool_names

        # Reference tools
        assert "list_custom_references" in tool_names
        assert "list_prebuilt_references" in tool_names

        # Total tool count
        assert len(tool_names) >= 25

    @pytest.mark.asyncio
    async def test_prompts_are_registered(self, mock_mcp_server):
        """Test that prompts are registered."""
        prompts = await mock_mcp_server.list_prompts()
        prompt_names = [prompt.name for prompt in prompts]

        assert "confirm_analysis_parameters" in prompt_names

    @pytest.mark.asyncio
    @patch('txg_cli_manager.txg_cli.run_command')
    async def test_auth_workflow(self, mock_run_command, mock_mcp_server):
        """Test authentication verification workflow."""
        import asyncio

        # Mock successful auth
        mock_run_command.return_value = AUTH_SUCCESS

        # Call the tool using call_tool method
        result_contents = await mock_mcp_server.call_tool("verify_auth", {})

        # Parse the result from the TextContent
        import json
        result = json.loads(result_contents[0].text)

        # Check result
        assert result["success"] is True
        assert "user@example.com" in result["content"]

    @pytest.mark.asyncio
    @patch('txg_cli_manager.txg_cli.run_command')
    async def test_failed_auth_workflow(self, mock_run_command, mock_mcp_server):
        """Test failed authentication handling."""
        import asyncio

        # Mock failed auth
        mock_run_command.return_value = AUTH_FAILURE

        # Call the tool
        result_contents = await mock_mcp_server.call_tool("verify_auth", {})

        # Parse the result from the TextContent
        import json
        result = json.loads(result_contents[0].text)

        # Check result
        assert result["success"] is False
        assert "Authentication failed" in result["error"]

    @pytest.mark.asyncio
    @patch('txg_cli_manager.txg_cli.run_command')
    async def test_analysis_creation_workflow(self, mock_run_command, mock_mcp_server):
        """Test complete analysis creation workflow."""
        import asyncio

        # Mock successful creation
        mock_run_command.return_value = ANALYSIS_CREATED

        # Call the tool
        result_contents = await mock_mcp_server.call_tool("create_cellranger_count_analysis", {
            "analysis_name": "test_analysis",
            "transcriptome": "GRCh38",
            "fastqs": ["test.fastq.gz"],
            "project_id": "project_123"
        })

        # Parse the result from the TextContent
        import json
        result = json.loads(result_contents[0].text)

        # Check result includes analysis response fields
        assert result["success"] is True
        assert "message" in result
        assert "next_steps" in result
        assert "Analysis started successfully" in result["message"]

    @pytest.mark.asyncio
    @patch('txg_cli_manager.txg_cli.run_command')
    async def test_list_operations(self, mock_run_command, mock_mcp_server):
        """Test list operations return proper JSON."""
        import asyncio

        # Mock project list
        mock_run_command.return_value = PROJECTS_LIST

        # Call the tool
        result_contents = await mock_mcp_server.call_tool("list_projects", {})

        # Parse the result from the TextContent
        import json
        result = json.loads(result_contents[0].text)

        # Check result
        assert result["success"] is True
        assert "project_123" in result["content"]
        assert "Test Project" in result["content"]

    @pytest.mark.asyncio
    async def test_tool_descriptions_reference_prompt(self, mock_mcp_server):
        """Test that analysis tools reference the confirmation prompt."""
        analysis_tools = [
            "create_cellranger_multi_analysis",
            "create_cellranger_count_analysis",
            "create_cellranger_aggr_analysis"
        ]

        tools_list = await mock_mcp_server.list_tools()
        tools = {t.name: t for t in tools_list}
        for tool_name in analysis_tools:
            # Check if the tool exists which means it was registered with the description
            assert tool_name in tools
            # Check that the description mentions the prompt
            tool = tools[tool_name]
            description = tool.description if hasattr(tool, 'description') else ""
            assert "confirm_analysis_parameters" in description or "MCP server prompt" in description