# tools.py
import requests
from langchain_core.tools import tool
from typing import Optional, List

# --- New Custom Decorator ---
def mcp_tool(command_prefix: tuple):
    """
    A custom decorator that wraps LangChain's @tool and adds a
    'mcp_command_prefix' attribute to the function for inspection.
    """
    def decorator(func):
        func.mcp_command_prefix = command_prefix
        # Apply the original @tool decorator to the function
        return tool(func)
    return decorator

# --- New Tool for User Interaction ---
@tool
def ask_user_for_input(question: str) -> str:
    """
    Asks the user a clarifying question and returns their input. 
    Use this tool when you need more information to proceed with a task.
    (This tool does not call the MCP server, so it doesn't need the custom decorator).
    """
    print(f"\n🤖 Agent asks: {question}")
    user_response = input("Your response: ")
    return user_response

# --- Helper Function ---
def call_mcp_server(command: list) -> str:
    """Helper function to call the local MCP server."""
    mcp_server_url = "http://127.0.0.1:5001/run_command"
    payload = {"command": command}
    try:
        response = requests.post(mcp_server_url, json=payload)
        response.raise_for_status()
        return response.json().get("content", "No content found in response.")
    except requests.exceptions.RequestException as e:
        return f"Error calling MCP server: {e}"

# --- Refactored Tools using the @mcp_tool decorator ---

@mcp_tool(command_prefix=("analyses", "create", "cellranger", "multi"))
def create_cellranger_multi_analysis(analysis_name: str, csv_path: str, project_id: Optional[str] = None, project_name: Optional[str] = None, description: Optional[str] = None, product_version: Optional[str] = None) -> str:
    """Creates a new Cell Ranger 'multi' analysis."""
    command = list(create_cellranger_multi_analysis.mcp_command_prefix) + ["--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes"]
    if project_id: command.extend(["--project-id", project_id])
    elif project_name: command.extend(["--project-name", project_name])
    if description: command.extend(["--description", description])
    if product_version: command.extend(["--product-version", product_version])
    return call_mcp_server(command)

@mcp_tool(command_prefix=("analyses", "create", "cellranger", "count"))
def create_cellranger_count_analysis(analysis_name: str, transcriptome: str, fastqs: List[str], project_id: Optional[str] = None, project_name: Optional[str] = None, expect_cells: Optional[int] = None, chemistry: Optional[str] = "auto") -> str:
    """Creates a new Cell Ranger 'count' analysis."""
    command = list(create_cellranger_count_analysis.mcp_command_prefix) + ["--analysis-name", analysis_name, "--transcriptome", transcriptome, "--assumeyes"]
    for fq_path in fastqs: command.extend(["--fastqs", fq_path])
    if project_id: command.extend(["--project-id", project_id])
    elif project_name: command.extend(["--project-name", project_name])
    if expect_cells: command.extend(["--expect-cells", str(expect_cells)])
    if chemistry: command.extend(["--chemistry", chemistry])
    return call_mcp_server(command)

@mcp_tool(command_prefix=("analyses", "create", "cellranger", "aggr"))
def create_cellranger_aggr_analysis(analysis_name: str, csv_path: str, project_id: Optional[str] = None, project_name: Optional[str] = None, normalize: Optional[str] = "mapped", description: Optional[str] = None) -> str:
    """Creates a new Cell Ranger 'aggr' analysis to aggregate multiple runs."""
    command = list(create_cellranger_aggr_analysis.mcp_command_prefix) + ["--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes"]
    if project_id: command.extend(["--project-id", project_id])
    elif project_name: command.extend(["--project-name", project_name])
    if normalize: command.extend(["--normalize", normalize])
    if description: command.extend(["--description", description])
    return call_mcp_server(command)

@mcp_tool(command_prefix=("analyses", "list"))
def list_analyses(project_id: str) -> str:
    """Lists all analyses in a specific project."""
    return call_mcp_server(list(list_analyses.mcp_command_prefix) + [project_id])

@mcp_tool(command_prefix=("analyses", "get"))
def get_analysis_details(analysis_id: str) -> str:
    """Shows details about a single analysis."""
    return call_mcp_server(list(get_analysis_details.mcp_command_prefix) + [analysis_id])

@mcp_tool(command_prefix=("analyses", "files"))
def list_analysis_files(analysis_id: str) -> str:
    """Lists all files within a single analysis."""
    return call_mcp_server(list(list_analysis_files.mcp_command_prefix) + [analysis_id])

@mcp_tool(command_prefix=("analyses", "download"))
def download_analysis_files(analysis_id: str, output_path: str) -> str:
    """Downloads all files from an analysis to a specified local path."""
    return call_mcp_server(list(download_analysis_files.mcp_command_prefix) + [analysis_id, "--output", output_path, "--assumeyes"])

@mcp_tool(command_prefix=("annotation", "models", "list"))
def list_annotation_models() -> str:
    """Lists available cell annotation models."""
    return call_mcp_server(list(list_annotation_models.mcp_command_prefix))

@mcp_tool(command_prefix=("fastqs", "list"))
def list_fastqs(project_id: str) -> str:
    """Lists FASTQ files for a given project."""
    return call_mcp_server(list(list_fastqs.mcp_command_prefix) + ["--project-id", project_id])

@mcp_tool(command_prefix=("fastqs", "upload"))
def upload_fastqs(project_id: str, file_path: str) -> str:
    """Uploads FASTQ files from a local path to a project."""
    return call_mcp_server(list(upload_fastqs.mcp_command_prefix) + ["--project-id", project_id, file_path, "--assumeyes"])

@mcp_tool(command_prefix=("files", "list"))
def list_project_files(project_id: str) -> str:
    """Lists general files for a given project."""
    return call_mcp_server(list(list_project_files.mcp_command_prefix) + ["--project-id", project_id])

@mcp_tool(command_prefix=("files", "upload"))
def upload_project_file(project_id: str, file_path: str) -> str:
    """Uploads a local file to a project."""
    return call_mcp_server(list(upload_project_file.mcp_command_prefix) + ["--project-id", project_id, file_path, "--assumeyes"])

@mcp_tool(command_prefix=("files", "download"))
def download_project_file(project_id: str, file_name: str, output_path: str) -> str:
    """Downloads a specific file from a project to a local path."""
    return call_mcp_server(list(download_project_file.mcp_command_prefix) + [file_name, "--project-id", project_id, "--output", output_path, "--assumeyes"])

@mcp_tool(command_prefix=("projects", "list"))
def list_projects() -> str:
    """Lists all available projects."""
    return call_mcp_server(list(list_projects.mcp_command_prefix))

@mcp_tool(command_prefix=("projects", "create"))
def create_project(name: str, description: Optional[str] = None) -> str:
    """Creates a new project with a given name and optional description."""
    command = list(create_project.mcp_command_prefix) + ["--name", name, "--assumeyes"]
    if description: command.extend(["--description", description])
    return call_mcp_server(command)

@mcp_tool(command_prefix=("projects", "update"))
def update_project(project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
    """Updates the name and/or description of an existing project."""
    command = list(update_project.mcp_command_prefix) + [project_id, "--assumeyes"]
    if name: command.extend(["--name", name])
    if description: command.extend(["--description", description])
    return call_mcp_server(command)

@mcp_tool(command_prefix=("references", "list"))
def list_references() -> str:
    """Lists all custom references."""
    return call_mcp_server(list(list_references.mcp_command_prefix))

@mcp_tool(command_prefix=("references", "get"))
def get_reference(reference_id: str) -> str:
    """Shows details for a specific custom reference."""
    return call_mcp_server(list(get_reference.mcp_command_prefix) + [reference_id])

@mcp_tool(command_prefix=("references", "update"))
def update_reference(reference_id: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
    """Updates the name and/or description for a custom reference."""
    command = list(update_reference.mcp_command_prefix) + [reference_id, "--assumeyes"]
    if name: command.extend(["--name", name])
    if description: command.extend(["--description", description])
    return call_mcp_server(command)

@mcp_tool(command_prefix=("references", "upload"))
def upload_reference(file_path: str, name: str, organism: str) -> str:
    """Uploads a custom reference from a local file path."""
    command = list(upload_reference.mcp_command_prefix) + [file_path, "--name", name, "--organism", organism, "--assumeyes"]
    return call_mcp_server(command)