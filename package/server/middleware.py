#!/usr/bin/env python3

from txg_cli_manager import CommandResult

def to_response(command_result: CommandResult) -> dict:
    """
    Convert raw command execution result tuple into formatted response dict.
    
    Args:
        command_result: Tuple of (stdout, stderr, returncode) from txg_cli.run_command()
        
    Returns:
        Dictionary with processed command results ready for client response
    """
    content, error, returncode, full_command = command_result
    
    # # Clean up output strings
    # cleaned_stdout = stdout.strip() if stdout else ""
    # cleaned_stderr = stderr.strip() if stderr else ""
    
    # TODO: Add filtering logic here later if needed
    # TODO: Add error code normalization if needed
    # TODO: Add logging/metrics if needed
    
    return {
        "content": content,
        "error": error,
        "returncode": returncode,
        "success": returncode == 0,
        "dbg-full-command": full_command  # TODO: Remove this debug field later
    }

def to_analysis_response(command_result: CommandResult) -> dict:
    """
    Convert analysis command result to formatted response with additional guidance.

    Adds helpful message and next steps for analysis jobs that run asynchronously.

    Args:
        command_result: Tuple of (stdout, stderr, returncode) from txg_cli.run_command()

    Returns:
        Dictionary with processed command results plus analysis-specific fields
    """
    response = to_response(command_result)

    if response["success"]:
        response["message"] = "Analysis started successfully. Expected completion time can be several hours depending on data size. The job will continue running even if this conversation ends."
        response["next_steps"] = "Use 'get_analysis_details' tool to check progress. You will receive an email notification when the analysis is complete."

    return response