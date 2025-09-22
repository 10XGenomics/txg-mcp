"""Tests for command building from tool parameters."""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from tests.fixtures.mock_responses import *

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "package"))
sys.path.insert(0, str(Path(__file__).parent.parent / "package" / "server"))

from txg_cli_manager import txg_cli

class TestCommandBuilding:
    """Test that tools build correct CLI commands."""

    @pytest.fixture
    def mock_txg_cli(self):
        """Mock the txg_cli.run_command method."""
        with patch.object(txg_cli, 'run_command') as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_create_cellranger_count_basic(self, mock_txg_cli):
        """Test basic Cell Ranger count command building."""
        from tools import register_tools
        from mcp.server.fastmcp import FastMCP

        # Create MCP instance and register tools
        mcp = FastMCP("test")
        register_tools(mcp)

        # Mock the CLI to return success
        mock_txg_cli.return_value = ANALYSIS_CREATED

        # Call the tool using call_tool
        result = await mcp.call_tool("create_cellranger_count_analysis", {
            "analysis_name": "test_analysis",
            "transcriptome": "GRCh38",
            "fastqs": ["sample_S1_L001_R1_001.fastq.gz"],
            "project_id": "project_123"
        })

        # Verify the command was built correctly
        mock_txg_cli.assert_called_once()
        command = mock_txg_cli.call_args[0][0]

        assert command[0:5] == ["analyses", "create", "cellranger", "count", "--analysis-name"]
        assert "test_analysis" in command
        assert "--transcriptome" in command
        assert "GRCh38" in command
        assert "--fastqs" in command
        assert "sample_S1_L001_R1_001.fastq.gz" in command
        assert "--project-id" in command
        assert "project_123" in command
        assert "--assumeyes" in command
        assert "--wait-completion=false" in command

    @pytest.mark.asyncio
    async def test_create_cellranger_count_with_optional_params(self, mock_txg_cli):
        """Test Cell Ranger count with optional parameters."""
        from tools import register_tools
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_tools(mcp)
        mock_txg_cli.return_value = ANALYSIS_CREATED

        # Call with optional parameters
        result = await mcp.call_tool("create_cellranger_count_analysis", {
            "analysis_name": "test_analysis",
            "transcriptome": "GRCh38",
            "fastqs": ["sample1.fastq.gz", "sample2.fastq.gz"],
            "project_name": "new_project",
            "expect_cells": 5000,
            "chemistry": "SC3Pv3"
        })

        command = mock_txg_cli.call_args[0][0]

        # Check optional parameters are included
        assert "--project-name" in command
        assert "new_project" in command
        assert "--expect-cells" in command
        assert "5000" in str(command)
        assert "--chemistry" in command
        assert "SC3Pv3" in command
        # Should have two fastq files
        fastq_count = command.count("--fastqs")
        assert fastq_count == 2

    @pytest.mark.asyncio
    async def test_create_cellranger_multi(self, mock_txg_cli):
        """Test Cell Ranger multi command building."""
        from tools import register_tools
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_tools(mcp)
        mock_txg_cli.return_value = ANALYSIS_CREATED

        result = await mcp.call_tool("create_cellranger_multi_analysis", {
            "analysis_name": "multi_test",
            "csv_path": "/path/to/config.csv",
            "project_id": "project_456",
            "description": "Test multi analysis",
            "product_version": "9.0.1"
        })

        command = mock_txg_cli.call_args[0][0]

        assert "cellranger" in command
        assert "multi" in command
        assert "--csv" in command
        assert "/path/to/config.csv" in command
        assert "--description" in command
        assert "Test multi analysis" in command
        assert "--product-version" in command
        assert "9.0.1" in command

    @pytest.mark.asyncio
    async def test_upload_fastqs_command(self, mock_txg_cli):
        """Test FASTQ upload command building."""
        from tools import register_tools
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_tools(mcp)
        mock_txg_cli.return_value = ("Upload successful", "", 0, "txg fastqs upload")

        result = await mcp.call_tool("upload_fastqs", {
            "project_id": "project_789",
            "file_path": "/data/fastqs/"
        })

        command = mock_txg_cli.call_args[0][0]

        assert command[0:2] == ["fastqs", "upload"]
        assert "--project-id" in command
        assert "project_789" in command
        assert "/data/fastqs/" in command
        assert "--assumeyes" in command

    @pytest.mark.asyncio
    async def test_list_commands_no_assumeyes(self, mock_txg_cli):
        """Test that list commands don't include --assumeyes."""
        from tools import register_tools
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_tools(mcp)
        mock_txg_cli.return_value = PROJECTS_LIST

        result = await mcp.call_tool("list_projects", {})
        command = mock_txg_cli.call_args[0][0]

        assert command == ["projects", "list"]
        assert "--assumeyes" not in command

    @pytest.mark.asyncio
    async def test_auth_verify_simple_command(self, mock_txg_cli):
        """Test auth verify builds simple command."""
        from tools import register_tools
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_tools(mcp)
        mock_txg_cli.return_value = AUTH_SUCCESS

        result = await mcp.call_tool("verify_auth", {})
        command = mock_txg_cli.call_args[0][0]

        assert command == ["auth", "verify"]