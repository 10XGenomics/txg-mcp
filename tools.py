# tools.py
import requests
from langchain_core.tools import tool
from typing import Optional

# --- Helper Function ---
def call_mcp_server(command: list) -> str:
    """
    Helper function to call the local MCP server by sending the full command.
    The MCP server will be updated to receive a list of command parts.
    """
    mcp_server_url = "http://127.0.0.1:5001/run_command" # Updated endpoint
    payload = {"command": command}
    try:
        response = requests.post(mcp_server_url, json=payload)
        response.raise_for_status()
        return response.json().get("content", "No content found in response.")
    except requests.exceptions.RequestException as e:
        return f"Error calling MCP server: {e}"

# --- Analyses Tools ---

@tool
def list_analyses(project_id: str) -> str:
    """Lists all analyses in a specific project."""
    return call_mcp_server(["analyses", "list", "--project-id", project_id])

@tool
def get_analysis_details(analysis_id: str) -> str:
    """Shows details about a single analysis."""
    return call_mcp_server(["analyses", "get", analysis_id])

@tool
def list_analysis_files(analysis_id: str) -> str:
    """Lists all files within a single analysis."""
    return call_mcp_server(["analyses", "files", analysis_id])

@tool
def download_analysis_files(analysis_id: str, output_path: str) -> str:
    """Downloads all files from an analysis to a specified local path."""
    return call_mcp_server(["analyses", "download", analysis_id, "--output", output_path])

# --- Annotation Tools ---

@tool
def list_annotation_models() -> str:
    """Lists available cell annotation models."""
    return call_mcp_server(["annotation", "models", "list"])

# --- FASTQ Tools ---

@tool
def list_fastqs(project_id: str) -> str:
    """Lists FASTQ files for a given project."""
    return call_mcp_server(["fastqs", "list", "--project-id", project_id])

@tool
def upload_fastqs(project_id: str, file_path: str) -> str:
    """Uploads FASTQ files from a local path to a project."""
    return call_mcp_server(["fastqs", "upload", "--project-id", project_id, file_path])

# --- File Management Tools ---

@tool
def list_project_files(project_id: str) -> str:
    """Lists general files for a given project."""
    return call_mcp_server(["files", "list", "--project-id", project_id])

@tool
def upload_project_file(project_id: str, file_path: str) -> str:
    """Uploads a local file to a project."""
    return call_mcp_server(["files", "upload", "--project-id", project_id, file_path])

@tool
def download_project_file(project_id: str, file_name: str, output_path: str) -> str:
    """Downloads a specific file from a project to a local path."""
    return call_mcp_server(["files", "download", file_name, "--project-id", project_id, "--output", output_path])

# --- Project Tools ---

@tool
def list_projects() -> str:
    """Lists all available projects."""
    return call_mcp_server(["projects", "list"])

@tool
def create_project(name: str, description: Optional[str] = None) -> str:
    """Creates a new project with a given name and optional description."""
    command = ["projects", "create", "--name", name]
    if description:
        command.extend(["--description", description])
    return call_mcp_server(command)

@tool
def update_project(project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
    """Updates the name and/or description of an existing project."""
    command = ["projects", "update", project_id]
    if name:
        command.extend(["--name", name])
    if description:
        command.extend(["--description", description])
    return call_mcp_server(command)

# --- Reference Tools ---

@tool
def list_references() -> str:
    """Lists all custom references."""
    return call_mcp_server(["references", "list"])

@tool
def get_reference(reference_id: str) -> str:
    """Shows details for a specific custom reference."""
    return call_mcp_server(["references", "get", reference_id])

@tool
def update_reference(reference_id: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
    """Updates the name and/or description for a custom reference."""
    command = ["references", "update", reference_id]
    if name:
        command.extend(["--name", name])
    if description:
        command.extend(["--description", description])
    return call_mcp_server(command)

@tool
def upload_reference(file_path: str, name: str, organism: str) -> str:
    """Uploads a custom reference from a local file path."""
    command = ["references", "upload", file_path, "--name", name, "--organism", organism]
    return call_mcp_server(command)
