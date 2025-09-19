#!/usr/bin/env python3

from typing import Optional, List, Annotated
from pydantic import Field
from txg_cli_manager import txg_cli
from middleware import to_response

def register_tools(mcp):
    """Register all 10x Genomics tools with the MCP server"""
    
    # --- Core Tools ---
    @mcp.tool(name="get_tool_version", description="Get the version of the TXG CLI tool.")
    async def get_tool_version() -> dict:
        return to_response(txg_cli.run_command(["--version"]))

    @mcp.tool(name="verify_auth", description="Verify authentication for the TXG CLI tool. Returns email of the authenticated user")
    async def verify_auth() -> dict:
        return to_response(txg_cli.run_command(["auth", "verify"]))
    
    # --- Analysis Tools ---
    @mcp.tool(name="create_cellranger_multi_analysis", description="Creates a new Cell Ranger 'multi' analysis.")
    async def create_cellranger_multi_analysis(
        analysis_name: Annotated[str, Field(description="Name of the analysis to create")], 
        csv_path: str, 
        project_id: Optional[str] = None, 
        project_name: Optional[str] = None, 
        description: Optional[str] = None, 
        product_version: Optional[str] = None
    ) -> dict:
        command = ["analyses", "create", "cellranger", "multi", "--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes"]
        if project_id: 
            command.extend(["--project-id", project_id])
        elif project_name: 
            command.extend(["--project-name", project_name])
        if description: 
            command.extend(["--description", description])
        if product_version: 
            command.extend(["--product-version", product_version])
        return to_response(txg_cli.run_command(command))

    @mcp.tool(name="create_cellranger_count_analysis", description="Creates a new Cell Ranger 'count' analysis.")
    async def create_cellranger_count_analysis(
        analysis_name: str, 
        transcriptome: str, 
        fastqs: List[str], 
        project_id: Optional[str] = None, 
        project_name: Optional[str] = None, 
        expect_cells: Optional[int] = None, 
        chemistry: Optional[str] = "auto"
    ) -> dict:
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
        return to_response(txg_cli.run_command(command))

    @mcp.tool(name="create_cellranger_aggr_analysis", description="Creates a new Cell Ranger 'aggr' analysis to aggregate multiple runs.")
    async def create_cellranger_aggr_analysis(
        analysis_name: str, 
        csv_path: str, 
        project_id: Optional[str] = None, 
        project_name: Optional[str] = None, 
        normalize: Optional[str] = "mapped", 
        description: Optional[str] = None
    ) -> dict:
        command = ["analyses", "create", "cellranger", "aggr", "--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes"]
        if project_id: 
            command.extend(["--project-id", project_id])
        elif project_name: 
            command.extend(["--project-name", project_name])
        if normalize: 
            command.extend(["--normalize", normalize])
        if description: 
            command.extend(["--description", description])
        return to_response(txg_cli.run_command(command))

    @mcp.tool(name="list_analyses", description="Lists all analyses in a specific project.")
    async def list_analyses(project_id: str) -> dict:
        return to_response(txg_cli.run_command(["analyses", "list", project_id]))

    @mcp.tool(name="get_analysis_details", description="Shows details about a single analysis.")
    async def get_analysis_details(analysis_id: str) -> dict:
        return to_response(txg_cli.run_command(["analyses", "get", analysis_id]))

    @mcp.tool(name="list_analysis_files", description="Lists all files within a single analysis.")
    async def list_analysis_files(analysis_id: str) -> dict:
        return to_response(txg_cli.run_command(["analyses", "files", analysis_id]))

    @mcp.tool(name="download_analysis_files", description="Downloads all files from an analysis to a specified local path.")
    async def download_analysis_files(analysis_id: str, output_path: str) -> dict:
        return to_response(txg_cli.run_command(["analyses", "download", analysis_id, "--output", output_path, "--assumeyes"]))

    # --- Annotation Tools ---
    @mcp.tool(name="list_annotation_models", description="Lists available cell annotation models.")
    async def list_annotation_models() -> dict:
        return to_response(txg_cli.run_command(["annotation", "models", "list"]))

    # --- FASTQ Tools ---
    @mcp.tool(name="list_fastqs", description="Lists FASTQ files for a given project.")
    async def list_fastqs(project_id: str) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "list", project_id]))

    @mcp.tool(name="upload_fastqs", description="Uploads FASTQ files from a local path to a project.")
    async def upload_fastqs(project_id: str, file_path: str) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "upload", "--project-id", project_id, file_path, "--assumeyes"]))

    @mcp.tool(name="list_libraries", description="List all available FASTQ libraries.")
    async def list_libraries(project_id: str) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "library"]))

    @mcp.tool(name="set_library", description="Set the library type for FASTQ sets.")
    async def set_library(project_id: str, fastq_id: str, library_type: str) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "library", "--project-id", project_id, fastq_id, library_type]))

    # --- File Management Tools ---
    @mcp.tool(name="list_project_files", description="Lists general files for a given project.")
    async def list_project_files(project_id: str) -> dict:
        return to_response(txg_cli.run_command(["files", "list", "--project-id", project_id]))

    @mcp.tool(name="upload_project_file", description="Uploads a local file to a project.")
    async def upload_project_file(project_id: str, file_path: str) -> dict:
        return to_response(txg_cli.run_command(["files", "upload", "--project-id", project_id, file_path, "--assumeyes"]))

    @mcp.tool(name="download_project_file", description="Downloads a specific file from a project to a local path.")
    async def download_project_file(project_id: str, file_name: str, output_path: str) -> dict:
        return to_response(txg_cli.run_command(["files", "download", file_name, "--project-id", project_id, "--output", output_path, "--assumeyes"]))

    # --- Project Management Tools ---
    @mcp.tool(name="list_projects", description="Lists all available projects.")
    async def list_projects() -> dict:
        return to_response(txg_cli.run_command(["projects", "list"]))

    @mcp.tool(name="create_project", description="Creates a new project with a given name and optional description.")
    async def create_project(name: str, description: Optional[str] = None) -> dict:
        command = ["projects", "create", "--name", name, "--assumeyes"]
        if description: 
            command.extend(["--description", description])
        return to_response(txg_cli.run_command(command))

    @mcp.tool(name="update_project", description="Updates the name and/or description of an existing project.")
    async def update_project(project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> dict:
        command = ["projects", "update", project_id, "--assumeyes"]
        if name: 
            command.extend(["--name", name])
        if description: 
            command.extend(["--description", description])
        return to_response(txg_cli.run_command(command))

    # --- Reference Management Tools ---
    @mcp.tool(name="list_references", description="Lists all custom references.")
    async def list_references() -> dict:
        return to_response(txg_cli.run_command(["references", "list"]))

    @mcp.tool(name="get_reference", description="Shows details for a specific custom reference.")
    async def get_reference(reference_id: str) -> dict:
        return to_response(txg_cli.run_command(["references", "get", reference_id]))

    @mcp.tool(name="update_reference", description="Updates the name and/or description for a custom reference.")
    async def update_reference(reference_id: str, name: Optional[str] = None, description: Optional[str] = None) -> dict:
        command = ["references", "update", reference_id, "--assumeyes"]
        if name: 
            command.extend(["--name", name])
        if description: 
            command.extend(["--description", description])
        return to_response(txg_cli.run_command(command))

    @mcp.tool(name="upload_reference", description="Uploads a custom reference from a local file path.")
    async def upload_reference(file_path: str, name: str, organism: str) -> dict:
        command = ["references", "upload", file_path, "--name", name, "--organism", organism, "--assumeyes"]
        return to_response(txg_cli.run_command(command))