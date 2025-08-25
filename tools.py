# tools.py
import requests
import json
from langchain_core.tools import tool

def call_mcp_server(tool_name: str, parameters: dict) -> str:
    """Helper function to call the local MCP server."""
    mcp_server_url = "http://127.0.0.1:5001/"
    payload = {
        "tool_name": tool_name,
        "parameters": parameters
    }
    try:
        response = requests.post(mcp_server_url, json=payload)
        response.raise_for_status()
        # Return the raw content from the server's response
        return response.json().get("content", "No content found in response.")
    except requests.exceptions.RequestException as e:
        return f"Error calling MCP server: {e}"

@tool
def list_projects() -> str:
    """Lists all available projects in 10x Genomics Cloud Analysis."""
    return call_mcp_server("list_projects", {})

@tool
def list_runs(project_id: str = None) -> str:
    """
    Lists analysis runs. Can be filtered by a specific project ID.
    Args:
        project_id (str, optional): The ID of the project to filter runs by.
    """
    params = {}
    if project_id:
        params["project_id"] = project_id
    return call_mcp_server("list_runs", params)

@tool
def get_run(run_id: str) -> str:
    """
    Retrieves the details for a specific analysis run by its ID.
    Args:
        run_id (str): The unique identifier of the run to retrieve.
    """
    return call_mcp_server("get_run", {"run_id": run_id})
