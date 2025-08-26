# tools.py
import requests
from langchain_core.tools import tool
from typing import Optional, List

# --- New Tool for User Interaction ---
@tool
def ask_user_for_input(question: str) -> str:
    """
    Asks the user a clarifying question and returns their input. 
    Use this tool when you need more information to proceed with a task.
    """
    print(f"\n🤖 Agent asks: {question}")
    user_response = input("Your response: ")
    return user_response

# --- Helper Function ---
def call_mcp_server(command: list) -> str:
    """
    Helper function to call the local MCP server by sending the full command.
    """
    mcp_server_url = "http://127.0.0.1:5001/run_command"
    payload = {"command": command}
    try:
        response = requests.post(mcp_server_url, json=payload)
        response.raise_for_status()
        return response.json().get("content", "No content found in response.")
    except requests.exceptions.RequestException as e:
        return f"Error calling MCP server: {e}"

# --- Analysis Creation Tools ---

@tool
def create_cellranger_multi_analysis(
    analysis_name: str,
    csv_path: str,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    description: Optional[str] = None,
    product_version: Optional[str] = None
) -> str:
    """Creates a new Cell Ranger 'multi' analysis."""
    command = ["analyses", "create", "cellranger", "multi", "--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes"]
    if project_id:
        command.extend(["--project-id", project_id])
    elif project_name:
        command.extend(["--project-name", project_name])
    if description:
        command.extend(["--description", description])
    if product_version:
        command.extend(["--product-version", product_version])
    return call_mcp_server(command)

@tool
def create_cellranger_count_analysis(
    analysis_name: str,
    transcriptome: str,
    fastqs: List[str],
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    expect_cells: Optional[int] = None,
    chemistry: Optional[str] = "auto"
) -> str:
    """Creates a new Cell Ranger 'count' analysis."""
    command = ["analyses", "create", "cellranger", "count", "--analysis-name", analysis_name, "--transcriptome", transcriptome, "--assumeyes"]
    for fq_path in fastqs:
        command.extend(["--fastqs", fq_path])
    if project_id:
        command.extend(["--project-id", project_id])
    elif project_name:
        command.extend(["--project-name", project_name])
    if expect_cells:
        command.extend(["--expect-cells", str(expect_cells)])
    if chemistry:
        command.extend(["--chemistry", chemistry])
    return call_mcp_server(command)

@tool
def create_cellranger_aggr_analysis(
    analysis_name: str,
    csv_path: str,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    normalize: Optional[str] = "mapped",
    description: Optional[str] = None
) -> str:
    """Creates a new Cell Ranger 'aggr' analysis to aggregate multiple runs."""
    command = ["analyses", "create", "cellranger", "aggr", "--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes"]
    if project_id:
        command.extend(["--project-id", project_id])
    elif project_name:
        command.extend(["--project-name", project_name])
    if normalize:
        command.extend(["--normalize", normalize])
    if description:
        command.extend(["--description", description])
    return call_mcp_server(command)

# --- Existing Tools ---

@tool
def list_analyses(project_id: str) -> str:
    """Lists all analyses in a specific project."""
    # Corrected to use a positional argument instead of the --project-id flag.
    return call_mcp_server(["analyses", "list", project_id])

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
    return call_mcp_server(["analyses", "download", analysis_id, "--output", output_path, "--assumeyes"])

@tool
def list_annotation_models() -> str:
    """Lists available cell annotation models."""
    return call_mcp_server(["annotation", "models", "list"])

@tool
def list_fastqs(project_id: str) -> str:
    """Lists FASTQ files for a given project."""
    return call_mcp_server(["fastqs", "list", "--project-id", project_id])

@tool
def upload_fastqs(project_id: str, file_path: str) -> str:
    """Uploads FASTQ files from a local path to a project."""
    return call_mcp_server(["fastqs", "upload", "--project-id", project_id, file_path, "--assumeyes"])

@tool
def list_project_files(project_id: str) -> str:
    """Lists general files for a given project."""
    return call_mcp_server(["files", "list", "--project-id", project_id])

@tool
def upload_project_file(project_id: str, file_path: str) -> str:
    """Uploads a local file to a project."""
    return call_mcp_server(["files", "upload", "--project-id", project_id, file_path, "--assumeyes"])

@tool
def download_project_file(project_id: str, file_name: str, output_path: str) -> str:
    """Downloads a specific file from a project to a local path."""
    return call_mcp_server(["files", "download", file_name, "--project-id", project_id, "--output", output_path, "--assumeyes"])

@tool
def list_projects() -> str:
    """Lists all available projects."""
    return call_mcp_server(["projects", "list"])

@tool
def create_project(name: str, description: Optional[str] = None) -> str:
    """Creates a new project with a given name and optional description."""
    command = ["projects", "create", "--name", name, "--assumeyes"]
    if description:
        command.extend(["--description", description])
    return call_mcp_server(command)

@tool
def update_project(project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
    """Updates the name and/or description of an existing project."""
    command = ["projects", "update", project_id, "--assumeyes"]
    if name:
        command.extend(["--name", name])
    if description:
        command.extend(["--description", description])
    return call_mcp_server(command)

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
    command = ["references", "update", reference_id, "--assumeyes"]
    if name:
        command.extend(["--name", name])
    if description:
        command.extend(["--description", description])
    return call_mcp_server(command)

@tool
def upload_reference(file_path: str, name: str, organism: str) -> str:
    """Uploads a custom reference from a local file path."""
    command = ["references", "upload", file_path, "--name", name, "--organism", organism, "--assumeyes"]
    return call_mcp_server(command)