/**
 * Type definitions for TXG MCP Server
 */

// Configuration types
export interface Config {
  readonly txgExecutable: string;
  readonly verboseLogging: boolean;
  readonly commandTimeout: number;
}

// Logging types
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

// Command types
export type AllowedCommand = 
  | 'analyses.create.cellranger.multi'
  | 'analyses.create.cellranger.count'
  | 'analyses.create.cellranger.aggr'
  | 'analyses.list'
  | 'analyses.get'
  | 'analyses.files'
  | 'analyses.download'
  | 'annotation.models.list'
  | 'fastqs.list'
  | 'fastqs.upload'
  | 'files.list'
  | 'files.upload'
  | 'files.download'
  | 'projects.list'
  | 'projects.create'
  | 'projects.update'
  | 'references.list'
  | 'references.get'
  | 'references.update'
  | 'references.upload';

// Tool argument types
export interface CreateCellrangerMultiArgs {
  analysis_name: string;
  csv_path: string;
  project_id?: string;
  project_name?: string;
  description?: string;
  product_version?: string;
}

export interface CreateCellrangerCountArgs {
  analysis_name: string;
  transcriptome: string;
  fastqs: string[];
  project_id?: string;
  project_name?: string;
  expect_cells?: number;
  chemistry?: string;
}

export interface CreateCellrangerAggrArgs {
  analysis_name: string;
  csv_path: string;
  project_id?: string;
  project_name?: string;
  normalize?: string;
  description?: string;
}

export interface ListAnalysesArgs {
  project_id: string;
}

export interface GetAnalysisDetailsArgs {
  analysis_id: string;
}

export interface ListAnalysisFilesArgs {
  analysis_id: string;
}

export interface DownloadAnalysisFilesArgs {
  analysis_id: string;
  output_path: string;
}

export interface ListFastqsArgs {
  project_id: string;
}

export interface UploadFastqsArgs {
  project_id: string;
  file_path: string;
}

export interface ListProjectFilesArgs {
  project_id: string;
}

export interface UploadProjectFileArgs {
  project_id: string;
  file_path: string;
}

export interface DownloadProjectFileArgs {
  project_id: string;
  file_name: string;
  output_path: string;
}

export interface CreateProjectArgs {
  name: string;
  description?: string;
}

export interface UpdateProjectArgs {
  project_id: string;
  name?: string;
  description?: string;
}

export interface GetReferenceArgs {
  reference_id: string;
}

export interface UpdateReferenceArgs {
  reference_id: string;
  name?: string;
  description?: string;
}

export interface UploadReferenceArgs {
  file_path: string;
  name: string;
  organism: string;
}

// Union type for all tool arguments
export type ToolArguments = 
  | CreateCellrangerMultiArgs
  | CreateCellrangerCountArgs
  | CreateCellrangerAggrArgs
  | ListAnalysesArgs
  | GetAnalysisDetailsArgs
  | ListAnalysisFilesArgs
  | DownloadAnalysisFilesArgs
  | ListFastqsArgs
  | UploadFastqsArgs
  | ListProjectFilesArgs
  | UploadProjectFileArgs
  | DownloadProjectFileArgs
  | CreateProjectArgs
  | UpdateProjectArgs
  | GetReferenceArgs
  | UpdateReferenceArgs
  | UploadReferenceArgs
  | Record<string, never>; // For tools with no arguments

// Tool definition types
export interface ToolInputProperty {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description?: string;
  default?: unknown;
  items?: { type: string };
  properties?: Record<string, ToolInputProperty>;
  required?: string[];
  enum?: string[];
  min?: number;
  max?: number;
}

export interface ToolInputSchema {
  type: 'object';
  properties: Record<string, ToolInputProperty>;
  required: string[];
}

export interface Tool<T extends ToolArguments = ToolArguments> {
  name: string;
  description: string;
  inputSchema: ToolInputSchema;
  handler: (args: T) => Promise<string>;
}

// Error types
export class TxgError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
    public readonly exitCode?: number
  ) {
    super(message);
    this.name = 'TxgError';
  }
}

export class ValidationError extends TxgError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

export class CommandNotAllowedError extends TxgError {
  constructor(command: string) {
    super(`Command not allowed: ${command}`, 'COMMAND_NOT_ALLOWED');
    this.name = 'CommandNotAllowedError';
  }
}

export class ExecutionError extends TxgError {
  constructor(message: string, exitCode?: number) {
    super(message, 'EXECUTION_ERROR', exitCode);
    this.name = 'ExecutionError';
  }
}

// Process execution types
export interface ExecutionResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

