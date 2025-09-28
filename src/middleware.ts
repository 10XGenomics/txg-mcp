import { CommandResult } from './txg-cli-manager.js';

export interface Response {
  content: string;
  error: string;
  returncode: number;
  success: boolean;
  fullCommand: string;
}

export interface AnalysisResponse extends Response {
  message?: string;
  next_steps?: string;
}

export function toResponse(result: CommandResult): Response {
  // When command succeeds, treat stderr as additional output, not an error
  // Some CLI tools output success messages to stderr
  const success = result.exitCode === 0;

  return {
    content: success ? (result.stdout || result.stderr).trim() : result.stdout,
    error: success ? '' : result.stderr,
    returncode: result.exitCode,
    success: success,
    fullCommand: result.fullCommand
  };
}

export function toAnalysisResponse(result: CommandResult): AnalysisResponse {
  const response = toResponse(result);

  if (response.success) {
    return {
      ...response,
      message: "Analysis started successfully. Expected completion time can be several hours depending on data size. The job will continue running even if this conversation ends.",
      next_steps: "Use 'get_analysis_details' tool to check progress. You will receive an email notification when the analysis is complete."
    };
  }

  return response;
}