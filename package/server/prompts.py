#!/usr/bin/env python3

def register_prompts(mcp):
    """Register all 10x Genomics prompts with the MCP server"""

    @mcp.prompt(name="confirm_analysis_parameters", description="Prompt to help LLMs confirm analysis parameters with users before creating an analysis. Always use this prompt before calling any create_cellranger_* tool to verify parameters with the user, unless explicitly told not to confirm for batch operations.")
    async def confirm_analysis_parameters(analysis_type: str, parameters: str) -> str:
        """
        Prompt to help LLMs confirm analysis parameters with users before submission.

        This prompt provides guidance on when to confirm parameters and when to skip confirmation
        for batch operations or experienced users.
        """
        return f"""You are about to create a {analysis_type} analysis with the following parameters:

{parameters}

IMPORTANT INSTRUCTIONS FOR THE ASSISTANT:

1. DEFAULT BEHAVIOR (Single Analysis):
   - ALWAYS confirm parameters with the user before calling any create_cellranger_* tool
   - Display all parameters clearly and ask: "Please review these parameters. Should I proceed with creating this analysis?"
   - Wait for explicit user confirmation before proceeding
   - This is critical because analyses can take several hours and consume significant compute resources

2. BATCH OPERATIONS (Multiple Analyses):
   - If the user explicitly states "no confirmation needed" or "don't confirm each one" or similar:
     - Skip individual confirmations and proceed with all analyses
     - Still show a summary of what will be created
   - If the user provides a CSV or structured list of analyses to run:
     - Confirm once for the entire batch, not for each individual analysis
   - Example: "run count analysis for each subfolder and no need to confirm" → Skip confirmations

3. PARAMETER VALIDATION:
   - Verify all required parameters are present
   - Check that reference genomes/transcriptomes exist (use list tools if needed)
   - Ensure FASTQ files are properly specified
   - Validate project IDs exist or new project names are provided

4. ERROR PREVENTION:
   - Double-check critical parameters that commonly cause failures:
     * Transcriptome/reference ID validity
     * FASTQ file paths or IDs
     * Chemistry settings (if not auto)
     * CSV file paths for multi/aggr analyses
   - If any parameter seems incorrect or missing, ask for clarification BEFORE confirming

Remember: It's better to confirm once and avoid hours of wasted compute than to proceed with wrong parameters."""