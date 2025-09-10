#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { 
  CallToolRequest,
  CallToolRequestSchema, 
  ListToolsRequestSchema
} from '@modelcontextprotocol/sdk/types.js';
import { spawn, ChildProcess } from 'child_process';
import {
  Config,
  LogLevel,
  AllowedCommand,
  Tool,
  ToolArguments,
  ValidationError,
  CommandNotAllowedError,
  ExecutionError,
  CreateCellrangerMultiArgs,
  CreateCellrangerCountArgs,
  CreateCellrangerAggrArgs,
  ListAnalysesArgs,
  GetAnalysisDetailsArgs,
  ListAnalysisFilesArgs,
  DownloadAnalysisFilesArgs,
  ListFastqsArgs,
  UploadFastqsArgs,
  ListProjectFilesArgs,
  UploadProjectFileArgs,
  DownloadProjectFileArgs,
  CreateProjectArgs,
  UpdateProjectArgs,
  GetReferenceArgs,
  UpdateReferenceArgs,
  UploadReferenceArgs
} from '../types/index.js';

// Configuration from environment variables with strong typing
// DXT passes user config as DXT_CONFIG_<NAME> environment variables
const CONFIG: Config = {
  txgExecutable: process.env['DXT_CONFIG_TXG_EXECUTABLE'] ?? process.env['TXG_EXECUTABLE'] ?? '/usr/local/bin/txg',
  verboseLogging: process.env['DXT_CONFIG_VERBOSE_LOGGING'] === 'true' || process.env['VERBOSE_LOGGING'] === 'true',
  commandTimeout: parseInt(process.env['DXT_CONFIG_COMMAND_TIMEOUT'] ?? process.env['COMMAND_TIMEOUT'] ?? '120000', 10)
} as const;

// Validate configuration
if (isNaN(CONFIG.commandTimeout) || CONFIG.commandTimeout < 0) {
  throw new Error('Invalid COMMAND_TIMEOUT value');
}

// Logger utility with type safety
const log = (message: string, level: LogLevel = 'info'): void => {
  if (CONFIG.verboseLogging || level === 'error') {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] [${level.toUpperCase()}] ${message}`);
  }
};

// Command allowlist with type safety
const ALLOWED_COMMANDS: ReadonlySet<AllowedCommand> = new Set<AllowedCommand>([
  'analyses.create.cellranger.multi',
  'analyses.create.cellranger.count',
  'analyses.create.cellranger.aggr',
  'analyses.list',
  'analyses.get',
  'analyses.files',
  'analyses.download',
  'annotation.models.list',
  'fastqs.list',
  'fastqs.upload',
  'files.list',
  'files.upload',
  'files.download',
  'projects.list',
  'projects.create',
  'projects.update',
  'references.list',
  'references.get',
  'references.update',
  'references.upload'
]);

// Validate command against allowlist with type safety
function validateCommand(commandParts: readonly string[]): void {
  const commandPrefix = commandParts.slice(0, Math.min(4, commandParts.length)).join('.');
  
  let isValid = false;
  for (const allowed of ALLOWED_COMMANDS) {
    if (allowed.startsWith(commandPrefix) || commandPrefix.startsWith(allowed)) {
      isValid = true;
      break;
    }
  }
  
  if (!isValid) {
    throw new CommandNotAllowedError(commandParts.join(' '));
  }
}

// Sanitize command arguments with strict validation
function sanitizeArgument(arg: string): string {
  const safePattern = /^[a-zA-Z0-9\/._\-\s]+$/;
  if (!safePattern.test(arg)) {
    throw new ValidationError(`Invalid characters in argument: ${arg}`);
  }
  return arg;
}

// Execute TXG command with strong typing and error handling
async function executeTxgCommand(commandParts: readonly string[]): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    try {
      // Validate command
      validateCommand(commandParts);
      
      // Sanitize all arguments
      const sanitizedParts = commandParts.map((part: string) => {
        // Skip flag arguments (start with --)
        if (part.startsWith('--')) {
          return part;
        }
        return sanitizeArgument(part);
      });
      
      const fullCommand = [CONFIG.txgExecutable, ...sanitizedParts];
      
      log(`Executing command: ${fullCommand.join(' ')}`, 'debug');
      
      const child: ChildProcess = spawn(fullCommand[0]!, fullCommand.slice(1), {
        timeout: CONFIG.commandTimeout,
        env: { ...process.env }
      });
      
      let stdout = '';
      let stderr = '';
      
      child.stdout?.on('data', (data: Buffer) => {
        const chunk = data.toString();
        stdout += chunk;
        if (CONFIG.verboseLogging) {
          process.stderr.write(chunk);
        }
      });
      
      child.stderr?.on('data', (data: Buffer) => {
        const chunk = data.toString();
        stderr += chunk;
        if (CONFIG.verboseLogging) {
          process.stderr.write(chunk);
        }
      });
      
      child.on('error', (error: Error) => {
        if ('code' in error && error.code === 'ENOENT') {
          reject(new ExecutionError(
            `TXG executable not found at ${CONFIG.txgExecutable}. Please ensure TXG CLI is installed.`
          ));
        } else {
          reject(new ExecutionError(`Failed to execute command: ${error.message}`));
        }
      });
      
      child.on('close', (code: number | null) => {
        if (code === 0) {
          resolve(stdout || 'Command executed successfully');
        } else {
          const errorMessage = stderr || stdout || `Command failed with exit code ${code}`;
          reject(new ExecutionError(errorMessage, code ?? undefined));
        }
      });
    } catch (error) {
      reject(error);
    }
  });
}

// Tool definitions with strong typing
const TOOLS: readonly Tool[] = [
  {
    name: 'create_cellranger_multi_analysis',
    description: 'Creates a new Cell Ranger "multi" analysis',
    inputSchema: {
      type: 'object',
      properties: {
        analysis_name: { type: 'string', description: 'Name for the analysis' },
        csv_path: { type: 'string', description: 'Path to the CSV configuration file' },
        project_id: { type: 'string', description: 'Project ID (optional)' },
        project_name: { type: 'string', description: 'Project name (optional, alternative to project_id)' },
        description: { type: 'string', description: 'Analysis description (optional)' },
        product_version: { type: 'string', description: 'Product version (optional)' }
      },
      required: ['analysis_name', 'csv_path']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as CreateCellrangerMultiArgs;
      const command: string[] = ['analyses', 'create', 'cellranger', 'multi', 
        '--analysis-name', typedArgs.analysis_name, 
        '--csv', typedArgs.csv_path, 
        '--assumeyes'
      ];
      if (typedArgs.project_id) command.push('--project-id', typedArgs.project_id);
      else if (typedArgs.project_name) command.push('--project-name', typedArgs.project_name);
      if (typedArgs.description) command.push('--description', typedArgs.description);
      if (typedArgs.product_version) command.push('--product-version', typedArgs.product_version);
      return await executeTxgCommand(command);
    }
  },
  {
    name: 'create_cellranger_count_analysis',
    description: 'Creates a new Cell Ranger "count" analysis',
    inputSchema: {
      type: 'object',
      properties: {
        analysis_name: { type: 'string', description: 'Name for the analysis' },
        transcriptome: { type: 'string', description: 'Reference transcriptome' },
        fastqs: { type: 'array', items: { type: 'string' }, description: 'FASTQ file paths' },
        project_id: { type: 'string', description: 'Project ID (optional)' },
        project_name: { type: 'string', description: 'Project name (optional)' },
        expect_cells: { type: 'number', description: 'Expected number of cells (optional)' },
        chemistry: { type: 'string', default: 'auto', description: 'Chemistry version (optional)' }
      },
      required: ['analysis_name', 'transcriptome', 'fastqs']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as CreateCellrangerCountArgs;
      const command: string[] = ['analyses', 'create', 'cellranger', 'count',
        '--analysis-name', typedArgs.analysis_name,
        '--transcriptome', typedArgs.transcriptome,
        '--assumeyes'
      ];
      typedArgs.fastqs.forEach(fq => command.push('--fastqs', fq));
      if (typedArgs.project_id) command.push('--project-id', typedArgs.project_id);
      else if (typedArgs.project_name) command.push('--project-name', typedArgs.project_name);
      if (typedArgs.expect_cells) command.push('--expect-cells', String(typedArgs.expect_cells));
      if (typedArgs.chemistry) command.push('--chemistry', typedArgs.chemistry);
      return await executeTxgCommand(command);
    }
  },
  {
    name: 'create_cellranger_aggr_analysis',
    description: 'Creates a new Cell Ranger "aggr" analysis to aggregate multiple runs',
    inputSchema: {
      type: 'object',
      properties: {
        analysis_name: { type: 'string', description: 'Name for the analysis' },
        csv_path: { type: 'string', description: 'Path to the aggregation CSV' },
        project_id: { type: 'string', description: 'Project ID (optional)' },
        project_name: { type: 'string', description: 'Project name (optional)' },
        normalize: { type: 'string', default: 'mapped', description: 'Normalization method (optional)' },
        description: { type: 'string', description: 'Analysis description (optional)' }
      },
      required: ['analysis_name', 'csv_path']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as CreateCellrangerAggrArgs;
      const command: string[] = ['analyses', 'create', 'cellranger', 'aggr',
        '--analysis-name', typedArgs.analysis_name,
        '--csv', typedArgs.csv_path,
        '--assumeyes'
      ];
      if (typedArgs.project_id) command.push('--project-id', typedArgs.project_id);
      else if (typedArgs.project_name) command.push('--project-name', typedArgs.project_name);
      if (typedArgs.normalize) command.push('--normalize', typedArgs.normalize);
      if (typedArgs.description) command.push('--description', typedArgs.description);
      return await executeTxgCommand(command);
    }
  },
  {
    name: 'list_analyses',
    description: 'Lists all analyses in a specific project',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      },
      required: ['project_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as ListAnalysesArgs;
      return await executeTxgCommand(['analyses', 'list', typedArgs.project_id]);
    }
  },
  {
    name: 'get_analysis_details',
    description: 'Shows details about a single analysis',
    inputSchema: {
      type: 'object',
      properties: {
        analysis_id: { type: 'string', description: 'Analysis ID' }
      },
      required: ['analysis_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as GetAnalysisDetailsArgs;
      return await executeTxgCommand(['analyses', 'get', typedArgs.analysis_id]);
    }
  },
  {
    name: 'list_analysis_files',
    description: 'Lists all files within a single analysis',
    inputSchema: {
      type: 'object',
      properties: {
        analysis_id: { type: 'string', description: 'Analysis ID' }
      },
      required: ['analysis_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as ListAnalysisFilesArgs;
      return await executeTxgCommand(['analyses', 'files', typedArgs.analysis_id]);
    }
  },
  {
    name: 'download_analysis_files',
    description: 'Downloads all files from an analysis to a specified local path',
    inputSchema: {
      type: 'object',
      properties: {
        analysis_id: { type: 'string', description: 'Analysis ID' },
        output_path: { type: 'string', description: 'Local directory path for downloads' }
      },
      required: ['analysis_id', 'output_path']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as DownloadAnalysisFilesArgs;
      return await executeTxgCommand([
        'analyses', 'download', typedArgs.analysis_id, 
        '--output', typedArgs.output_path, '--assumeyes'
      ]);
    }
  },
  {
    name: 'list_annotation_models',
    description: 'Lists available cell annotation models',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    },
    handler: async (): Promise<string> => {
      return await executeTxgCommand(['annotation', 'models', 'list']);
    }
  },
  {
    name: 'list_fastqs',
    description: 'Lists FASTQ files for a given project',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      },
      required: ['project_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as ListFastqsArgs;
      return await executeTxgCommand(['fastqs', 'list', '--project-id', typedArgs.project_id]);
    }
  },
  {
    name: 'upload_fastqs',
    description: 'Uploads FASTQ files from a local path to a project',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' },
        file_path: { type: 'string', description: 'Path to FASTQ file or directory' }
      },
      required: ['project_id', 'file_path']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as UploadFastqsArgs;
      return await executeTxgCommand([
        'fastqs', 'upload', '--project-id', typedArgs.project_id, 
        typedArgs.file_path, '--assumeyes'
      ]);
    }
  },
  {
    name: 'list_project_files',
    description: 'Lists general files for a given project',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      },
      required: ['project_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as ListProjectFilesArgs;
      return await executeTxgCommand(['files', 'list', '--project-id', typedArgs.project_id]);
    }
  },
  {
    name: 'upload_project_file',
    description: 'Uploads a local file to a project',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' },
        file_path: { type: 'string', description: 'Path to file to upload' }
      },
      required: ['project_id', 'file_path']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as UploadProjectFileArgs;
      return await executeTxgCommand([
        'files', 'upload', '--project-id', typedArgs.project_id, 
        typedArgs.file_path, '--assumeyes'
      ]);
    }
  },
  {
    name: 'download_project_file',
    description: 'Downloads a specific file from a project to a local path',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' },
        file_name: { type: 'string', description: 'Name of file to download' },
        output_path: { type: 'string', description: 'Local path for downloaded file' }
      },
      required: ['project_id', 'file_name', 'output_path']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as DownloadProjectFileArgs;
      return await executeTxgCommand([
        'files', 'download', typedArgs.file_name, 
        '--project-id', typedArgs.project_id, 
        '--output', typedArgs.output_path, '--assumeyes'
      ]);
    }
  },
  {
    name: 'list_projects',
    description: 'Lists all available projects',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    },
    handler: async (): Promise<string> => {
      return await executeTxgCommand(['projects', 'list']);
    }
  },
  {
    name: 'create_project',
    description: 'Creates a new project with a given name and optional description',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Project name' },
        description: { type: 'string', description: 'Project description (optional)' }
      },
      required: ['name']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as CreateProjectArgs;
      const command: string[] = ['projects', 'create', '--name', typedArgs.name, '--assumeyes'];
      if (typedArgs.description) command.push('--description', typedArgs.description);
      return await executeTxgCommand(command);
    }
  },
  {
    name: 'update_project',
    description: 'Updates the name and/or description of an existing project',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' },
        name: { type: 'string', description: 'New project name (optional)' },
        description: { type: 'string', description: 'New project description (optional)' }
      },
      required: ['project_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as UpdateProjectArgs;
      const command: string[] = ['projects', 'update', typedArgs.project_id, '--assumeyes'];
      if (typedArgs.name) command.push('--name', typedArgs.name);
      if (typedArgs.description) command.push('--description', typedArgs.description);
      return await executeTxgCommand(command);
    }
  },
  {
    name: 'list_references',
    description: 'Lists all custom references',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    },
    handler: async (): Promise<string> => {
      return await executeTxgCommand(['references', 'list']);
    }
  },
  {
    name: 'get_reference',
    description: 'Shows details for a specific custom reference',
    inputSchema: {
      type: 'object',
      properties: {
        reference_id: { type: 'string', description: 'Reference ID' }
      },
      required: ['reference_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as GetReferenceArgs;
      return await executeTxgCommand(['references', 'get', typedArgs.reference_id]);
    }
  },
  {
    name: 'update_reference',
    description: 'Updates the name and/or description for a custom reference',
    inputSchema: {
      type: 'object',
      properties: {
        reference_id: { type: 'string', description: 'Reference ID' },
        name: { type: 'string', description: 'New reference name (optional)' },
        description: { type: 'string', description: 'New reference description (optional)' }
      },
      required: ['reference_id']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as UpdateReferenceArgs;
      const command: string[] = ['references', 'update', typedArgs.reference_id, '--assumeyes'];
      if (typedArgs.name) command.push('--name', typedArgs.name);
      if (typedArgs.description) command.push('--description', typedArgs.description);
      return await executeTxgCommand(command);
    }
  },
  {
    name: 'upload_reference',
    description: 'Uploads a custom reference from a local file path',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: { type: 'string', description: 'Path to reference file' },
        name: { type: 'string', description: 'Reference name' },
        organism: { type: 'string', description: 'Organism name' }
      },
      required: ['file_path', 'name', 'organism']
    },
    handler: async (args: ToolArguments): Promise<string> => {
      const typedArgs = args as UploadReferenceArgs;
      return await executeTxgCommand([
        'references', 'upload', typedArgs.file_path, 
        '--name', typedArgs.name, 
        '--organism', typedArgs.organism, '--assumeyes'
      ]);
    }
  }
] as const;

// Create MCP server with type safety
const server = new Server(
  {
    name: 'txg-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema as unknown as Record<string, unknown>
    }))
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request: CallToolRequest) => {
  const { name, arguments: args } = request.params;
  
  log(`Executing tool: ${name}`, 'info');
  
  const tool = TOOLS.find(t => t.name === name);
  
  if (!tool) {
    throw new Error(`Unknown tool: ${name}`);
  }
  
  try {
    const result = await tool.handler((args || {}) as ToolArguments);
    
    return {
      content: [
        {
          type: 'text',
          text: result
        }
      ]
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    log(`Tool execution failed: ${errorMessage}`, 'error');
    throw error;
  }
});

// Start the server with proper error handling
async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  
  log('Starting TXG MCP server (TypeScript version)...', 'info');
  log(`TXG executable: ${CONFIG.txgExecutable}`, 'info');
  log(`Command timeout: ${CONFIG.commandTimeout}ms`, 'info');
  
  await server.connect(transport);
  
  log('TXG MCP server started successfully', 'info');
  
  // Handle graceful shutdown
  const shutdown = async (signal: string): Promise<void> => {
    log(`Received ${signal}, shutting down server...`, 'info');
    await server.close();
    process.exit(0);
  };
  
  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
}

// Run the server with proper error handling
main().catch((error: unknown) => {
  const errorMessage = error instanceof Error ? error.message : String(error);
  log(`Failed to start server: ${errorMessage}`, 'error');
  console.error(error);
  process.exit(1);
});