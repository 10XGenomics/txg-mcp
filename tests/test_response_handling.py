"""Tests for response transformation and error handling."""

import pytest
import sys
from pathlib import Path
from tests.fixtures.mock_responses import *

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "package"))
sys.path.insert(0, str(Path(__file__).parent.parent / "package" / "server"))

from middleware import to_response, to_analysis_response

class TestResponseHandling:
    """Test response transformation functions."""

    def test_to_response_success(self):
        """Test successful response transformation."""
        result = to_response(VERSION_INFO)

        assert result["success"] is True
        assert result["content"] == "txg version 1.2.3"
        assert result["error"] == ""
        assert result["returncode"] == 0
        assert "dbg-full-command" in result

    def test_to_response_failure(self):
        """Test failed response transformation."""
        result = to_response(AUTH_FAILURE)

        assert result["success"] is False
        assert result["content"] == ""
        assert "Authentication failed" in result["error"]
        assert result["returncode"] == 1

    def test_to_response_with_stderr_warning(self):
        """Test response with stderr but success code."""
        command_result = (
            "Operation completed",
            "Warning: This is a warning",
            0,
            "txg some command"
        )
        result = to_response(command_result)

        assert result["success"] is True
        assert result["content"] == "Operation completed"
        assert result["error"] == "Warning: This is a warning"
        assert result["returncode"] == 0

    def test_to_analysis_response_success(self):
        """Test analysis response adds extra fields on success."""
        result = to_analysis_response(ANALYSIS_CREATED)

        assert result["success"] is True
        assert "message" in result
        assert "Analysis started successfully" in result["message"]
        assert "next_steps" in result
        assert "get_analysis_details" in result["next_steps"]
        assert "email notification" in result["next_steps"]

    def test_to_analysis_response_failure(self):
        """Test analysis response doesn't add fields on failure."""
        failed_result = (
            "",
            "Error: Invalid parameters",
            1,
            "txg analyses create"
        )
        result = to_analysis_response(failed_result)

        assert result["success"] is False
        assert "message" not in result
        assert "next_steps" not in result
        assert result["error"] == "Error: Invalid parameters"

    def test_json_response_parsing(self):
        """Test that JSON responses are preserved."""
        result = to_response(PROJECTS_LIST)

        assert result["success"] is True
        # Content should be the raw JSON string
        assert '"id": "project_123"' in result["content"]
        assert result["error"] == ""

    def test_empty_response_handling(self):
        """Test handling of empty responses."""
        result = to_response(EMPTY_LIST)

        assert result["success"] is True
        assert result["content"] == "[]"
        assert result["error"] == ""

    def test_multiline_output_preserved(self):
        """Test that multiline output is preserved."""
        multiline_result = (
            "Line 1\nLine 2\nLine 3",
            "",
            0,
            "txg test"
        )
        result = to_response(multiline_result)

        assert result["success"] is True
        assert "Line 1\nLine 2\nLine 3" in result["content"]
        assert result["content"].count("\n") == 2

    def test_special_characters_handling(self):
        """Test that special characters are preserved."""
        special_result = (
            'Result with "quotes" and \'apostrophes\' and $pecial ch@rs!',
            "",
            0,
            "txg test"
        )
        result = to_response(special_result)

        assert result["success"] is True
        assert '"quotes"' in result["content"]
        assert "'apostrophes'" in result["content"]
        assert "$pecial ch@rs!" in result["content"]

    def test_error_code_mapping(self):
        """Test different error codes are handled."""
        error_codes = [
            (1, "General error"),
            (2, "Invalid command"),
            (127, "Command not found"),
            (255, "Unknown error")
        ]

        for code, error_msg in error_codes:
            result = to_response(("", error_msg, code, "txg test"))
            assert result["success"] is False
            assert result["returncode"] == code
            assert result["error"] == error_msg