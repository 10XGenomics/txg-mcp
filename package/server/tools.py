#!/usr/bin/env python3

from typing import Optional, List, Annotated
from pydantic import Field
from txg_cli_manager import txg_cli
from middleware import to_response, to_analysis_response

def register_tools(mcp):
    """Register all 10x Genomics tools with the MCP server"""
    
    # --- Core Tools ---
    @mcp.tool(name="get_tool_version", description="Get the version of the TXG CLI tool.")
    async def get_tool_version() -> dict:
        return to_response(txg_cli.run_command(["--version"]))

    @mcp.tool(name="verify_auth", description="Verify authentication for the TXG CLI tool. Returns email of the authenticated user. If authentication fails, instruct the user to update the token in Claude Desktop settings > Extensions > 10x Genomics Cloud Analysis.")
    async def verify_auth() -> dict:
        return to_response(txg_cli.run_command(["auth", "verify"]))
    
    # --- Analysis Tools ---
    @mcp.tool(name="create_cellranger_multi_analysis", description="Creates a new Cell Ranger 'multi' analysis.")
    async def create_cellranger_multi_analysis(
        analysis_name: Annotated[str, Field(description="Name of the analysis to create")],
        csv_path: Annotated[str, Field(description="Path to the multi config CSV file that defines the analysis parameters. Specification can be found at https://www.10xgenomics.com/support/software/cell-ranger/latest/analysis/inputs/cr-multi-config-csv-opts")],
        project_id: Annotated[Optional[str], Field(description="ID of existing project to create the analysis in. Either project_id or project_name must be specified")] = None,
        project_name: Annotated[Optional[str], Field(description="Name of a new project to create for this analysis (alternative to project_id)")] = None,
        description: Optional[str] = None,
        product_version: Annotated[Optional[str], Field(description="Specific Cell Ranger version to use (e.g., '9.0.1')")] = None
    ) -> dict:
        command = ["analyses", "create", "cellranger", "multi", "--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes", "--wait-completion=false"]
        if project_id: 
            command.extend(["--project-id", project_id])
        elif project_name: 
            command.extend(["--project-name", project_name])
        if description: 
            command.extend(["--description", description])
        if product_version: 
            command.extend(["--product-version", product_version])
        return to_analysis_response(txg_cli.run_command(command))

    @mcp.tool(name="create_cellranger_count_analysis", description="Creates a new Cell Ranger 'count' analysis.")
    async def create_cellranger_count_analysis(
        analysis_name: Annotated[str, Field(description="Name of the analysis to create")],
        transcriptome: Annotated[str, Field(description="Reference transcriptome to use (e.g., 'refdata-cellranger-GRCh38-2024-A', or custom reference ID). Use the 'list_custom_references' or 'list_prebuilt_references' tools to find available references.")],
        fastqs: Annotated[List[str], Field(description="List of FASTQ file paths or FASTQ set IDs to analyze. Can be local paths or previously uploaded FASTQ set IDs in the format txg://fastqs/<filename> or txg://fastqs/<fastq_uuid>")],
        project_id: Annotated[Optional[str], Field(description="ID of existing project to create the analysis in")] = None,
        project_name: Annotated[Optional[str], Field(description="Name of a new project to create for this analysis (alternative to project_id)")] = None,
        expect_cells: Annotated[Optional[int], Field(description="Expected number of cells (overrides auto-detection)")] = None,
        chemistry: Annotated[Optional[str], Field(description="Assay chemistry version (default: 'auto' for automatic detection)")] = "auto"
    ) -> dict:
        command = ["analyses", "create", "cellranger", "count", "--analysis-name", analysis_name, "--transcriptome", transcriptome, "--assumeyes", "--wait-completion=false"]
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
        return to_analysis_response(txg_cli.run_command(command))

    @mcp.tool(name="create_cellranger_aggr_analysis", description="Creates a new Cell Ranger 'aggr' analysis to aggregate multiple runs.")
    async def create_cellranger_aggr_analysis(
        analysis_name: Annotated[str, Field(description="Name of the aggregation analysis to create")],
        csv_path: Annotated[str, Field(description="Path to CSV file listing the analysis IDs to aggregate")],
        project_id: Annotated[Optional[str], Field(description="ID of existing project to create the analysis in")] = None,
        project_name: Annotated[Optional[str], Field(description="Name of a new project to create for this analysis (alternative to project_id)")] = None,
        normalize: Annotated[Optional[str], Field(description="Normalization method: 'mapped' (default) or 'none'")] = "mapped",
        description: Optional[str] = None
    ) -> dict:
        command = ["analyses", "create", "cellranger", "aggr", "--analysis-name", analysis_name, "--csv", csv_path, "--assumeyes", "--wait-completion=false"]
        if project_id:
            command.extend(["--project-id", project_id])
        elif project_name: 
            command.extend(["--project-name", project_name])
        if normalize:
            command.extend(["--normalize", normalize])
        if description:
            command.extend(["--description", description])
        return to_analysis_response(txg_cli.run_command(command))

    @mcp.tool(name="list_analyses", description="Lists all analyses in a specific project.")
    async def list_analyses(
        project_id: Annotated[str, Field(description="Project ID to list analyses from")]
    ) -> dict:
        return to_response(txg_cli.run_command(["analyses", "list", project_id]))

    @mcp.tool(name="get_analysis_details", description="Shows details about a single analysis.")
    async def get_analysis_details(
        analysis_id: Annotated[str, Field(description="Analysis ID to get details for")]
    ) -> dict:
        return to_response(txg_cli.run_command(["analyses", "get", analysis_id]))

    @mcp.tool(name="list_analysis_files", description="Lists all files within a single analysis.")
    async def list_analysis_files(
        analysis_id: Annotated[str, Field(description="Analysis ID to list files from")]
    ) -> dict:
        return to_response(txg_cli.run_command(["analyses", "files", analysis_id]))

    @mcp.tool(name="download_analysis_files", description="Downloads all files from an analysis to a specified local path.")
    async def download_analysis_files(
        analysis_id: Annotated[str, Field(description="Analysis ID to download files from")],
        output_path: Annotated[str, Field(description="Local directory path where files will be saved")]
    ) -> dict:
        return to_response(txg_cli.run_command(["analyses", "download", analysis_id, "--output", output_path, "--assumeyes"]))

    # --- Annotation Tools ---
    @mcp.tool(name="list_annotation_models", description="Lists available cell annotation models.")
    async def list_annotation_models() -> dict:
        return to_response(txg_cli.run_command(["annotation", "models", "list"]))

    # --- FASTQ Tools ---
    @mcp.tool(name="list_fastqs", description="Lists FASTQ files for a given project.")
    async def list_fastqs(
        project_id: Annotated[str, Field(description="Project ID to list FASTQ files from")]
    ) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "list", project_id]))

    @mcp.tool(name="upload_fastqs", description="Uploads FASTQ files from a local path to a project.")
    async def upload_fastqs(
        project_id: Annotated[str, Field(description="Project ID to upload FASTQ files to")],
        file_path: Annotated[str, Field(description="Path to FASTQ file(s) or directory containing FASTQ files. Files must follow Illumina naming convention (e.g., sample_S1_L001_R1_001.fastq.gz)")]
    ) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "upload", "--project-id", project_id, file_path, "--assumeyes"]))

    @mcp.tool(name="list_libraries", description="List all available FASTQ libraries.")
    async def list_libraries(
        project_id: Annotated[str, Field(description="Project ID to list FASTQ libraries from")]
    ) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "library"]))

    @mcp.tool(name="set_library", description="Set the library type for FASTQ sets.")
    async def set_library(
        project_id: Annotated[str, Field(description="Project ID containing the FASTQ set")],
        fastq_id: Annotated[str, Field(description="FASTQ set ID to update")],
        library_type: Annotated[str, Field(description="Library type to set. To get available types, use the 'list_libraries' tool." )]
    ) -> dict:
        return to_response(txg_cli.run_command(["fastqs", "library", "--project-id", project_id, fastq_id, library_type]))

    # --- File Management Tools ---
    @mcp.tool(name="list_project_files", description="Lists files for a given project.")
    async def list_project_files(
        project_id: Annotated[str, Field(description="Project ID to list files from")]
    ) -> dict:
        return to_response(txg_cli.run_command(["files", "list", "--project-id", project_id]))

    @mcp.tool(name="upload_project_file", description="Uploads a local file to a project.")
    async def upload_project_file(
        project_id: Annotated[str, Field(description="Project ID to upload file to")],
        file_path: Annotated[str, Field(description="Path to the local file to upload")]
    ) -> dict:
        return to_response(txg_cli.run_command(["files", "upload", "--project-id", project_id, file_path, "--assumeyes"]))

    @mcp.tool(name="download_project_file", description="Downloads a specific file from a project to a local path.")
    async def download_project_file(
        project_id: Annotated[str, Field(description="Project ID containing the file")],
        file_name: Annotated[str, Field(description="Name of the file to download from the project")],
        output_path: Annotated[str, Field(description="Local directory path where the file will be saved")]
    ) -> dict:
        return to_response(txg_cli.run_command(["files", "download", file_name, "--project-id", project_id, "--output", output_path, "--assumeyes"]))

    # --- Project Management Tools ---
    @mcp.tool(name="list_projects", description="Lists all available projects.")
    async def list_projects() -> dict:
        return to_response(txg_cli.run_command(["projects", "list"]))

    @mcp.tool(name="create_project", description="Creates a new project with a given name and optional description.")
    async def create_project(
        name: Annotated[str, Field(description="Name for the new project")],
        description: Optional[str] = None
    ) -> dict:
        command = ["projects", "create", "--name", name, "--assumeyes"]
        if description: 
            command.extend(["--description", description])
        return to_response(txg_cli.run_command(command))

    @mcp.tool(name="update_project", description="Updates the name and/or description of an existing project.")
    async def update_project(
        project_id: Annotated[str, Field(description="Project ID to update")],
        name: Annotated[Optional[str], Field(description="New name for the project")] = None,
        description: Optional[str] = None
    ) -> dict:
        command = ["projects", "update", project_id, "--assumeyes"]
        if name: 
            command.extend(["--name", name])
        if description: 
            command.extend(["--description", description])
        return to_response(txg_cli.run_command(command))

    # --- Reference Management Tools ---
    @mcp.tool(name="list_custom_references", description="Lists all custom references.")
    async def list_custom_references() -> dict:
        return to_response(txg_cli.run_command(["references", "list"]))
    
    @mcp.tool(name="list_prebuilt_references", description="Lists all prebuilt references.")
    async def list_prebuilt_references() -> dict:
        return to_response(txg_cli.run_command(["prebuilt-reference"]))

    @mcp.tool(name="get_reference", description="Shows details for a specific custom reference.")
    async def get_reference(
        reference_id: Annotated[str, Field(description="Reference ID to get details for")]
    ) -> dict:
        return to_response(txg_cli.run_command(["references", "get", reference_id]))

    @mcp.tool(name="update_reference", description="Updates the name and/or description for a custom reference.")
    async def update_reference(
        reference_id: Annotated[str, Field(description="Reference ID to update")],
        name: Annotated[Optional[str], Field(description="New name for the reference")] = None,
        description: Optional[str] = None
    ) -> dict:
        command = ["references", "update", reference_id, "--assumeyes"]
        if name: 
            command.extend(["--name", name])
        if description: 
            command.extend(["--description", description])
        return to_response(txg_cli.run_command(command))

    @mcp.tool(name="upload_reference", description="Uploads a custom reference from a local file path.")
    async def upload_reference(
        file_path: Annotated[str, Field(description="Path to reference file: can be a cellranger mkref/mkvdjref folder, .tar.gz file, or feature/probeset .CSV file")],
        name: Annotated[str, Field(description="Name for the custom reference")],
        organism: Annotated[str, Field(description="Organism name (e.g., 'Human', 'Mouse', or custom species name)")]
    ) -> dict:
        command = ["references", "upload", file_path, "--name", name, "--organism", organism, "--assumeyes"]
        return to_response(txg_cli.run_command(command))