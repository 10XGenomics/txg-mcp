/**
 * Tests for command building from tool parameters.
 */

import { jest } from '@jest/globals';
import { registerTools } from '../../src/tools';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import * as txgCliManager from '../../src/txg-cli-manager';
import { assertCommandContains, assertCommandInOrder } from '../fixtures/test-helpers';

// We use a dummy response for all tests since we're only testing
// the command building logic, not the response handling
const DUMMY_RESPONSE = {
  stdout: '',
  stderr: '',
  exitCode: 0,
  fullCommand: 'not-relevant-for-these-tests'
};

describe('Command Building Tests', () => {
  // These tests verify that the tool handlers in tools.ts correctly
  // transform MCP tool parameters into CLI command arguments.
  // We spy on txgCli.runCommand to capture what commands would be executed.

  let server: Server;
  let mockRunCommand: jest.MockedFunction<typeof txgCliManager.txgCli.runCommand>;
  let toolHandler: any;

  beforeEach(() => {
    server = new Server(
      { name: 'test-server', version: '1.0.0' },
      { capabilities: { tools: {}, prompts: {} } }
    );

    // Capture the handler when it's registered
    const originalSetRequestHandler = server.setRequestHandler.bind(server);
    server.setRequestHandler = function(schema: any, handler: any) {
      if (schema === CallToolRequestSchema) {
        toolHandler = handler;
      }
      return originalSetRequestHandler(schema, handler);
    };

    // Mock the runCommand method
    mockRunCommand = jest.spyOn(txgCliManager.txgCli, 'runCommand').mockImplementation(
      async (args: string[]) => {
        return {
          stdout: '',
          stderr: '',
          exitCode: 0,
          fullCommand: `txg ${args.join(' ')}`
        };
      }
    ) as jest.MockedFunction<typeof txgCliManager.txgCli.runCommand>;

    registerTools(server);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Cell Ranger Count Analysis', () => {
    it('should transform MCP parameters to CLI command correctly', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      // Call the tool with MCP-style parameters
      await toolHandler({
        params: {
          name: 'create_cellranger_count_analysis',
          arguments: {
            analysis_name: 'test_analysis',
            transcriptome: 'GRCh38',
            fastqs: ['sample_S1_L001_R1_001.fastq.gz'],
            project_id: 'project_123'
          }
        }
      } as any);

      // Verify the command that would be sent to the CLI
      expect(mockRunCommand).toHaveBeenCalledTimes(1);
      const command = mockRunCommand.mock.calls[0][0];

      // The tool should build this exact command structure
      expect(command.slice(0, 5)).toEqual(['analyses', 'create', 'cellranger', 'count', '--analysis-name']);
      expect(command[5]).toBe('test_analysis');

      // Verify all required parameters are correctly formatted
      assertCommandContains(command,
        '--transcriptome', 'GRCh38',
        '--fastqs', 'sample_S1_L001_R1_001.fastq.gz',
        '--project-id', 'project_123',
        '--assumeyes',
        '--wait-completion=false'
      );
    });

    it('should handle optional parameters correctly', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'create_cellranger_count_analysis',
          arguments: {
            analysis_name: 'test_analysis',
            transcriptome: 'GRCh38',
            fastqs: ['sample1.fastq.gz', 'sample2.fastq.gz'],
            project_name: 'new_project',
            expect_cells: 5000,
            chemistry: 'SC3Pv3'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandContains(command,
        '--project-name', 'new_project',
        '--expect-cells', '5000',
        '--chemistry', 'SC3Pv3'
      );

      // Should have two fastq entries
      const fastqIndices = command.reduce((indices: number[], item, index) => {
        if (item === '--fastqs') indices.push(index);
        return indices;
      }, []);
      expect(fastqIndices.length).toBe(2);
    });

    it('should prefer project_id over project_name when both provided', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'create_cellranger_count_analysis',
          arguments: {
            analysis_name: 'test',
            transcriptome: 'GRCh38',
            fastqs: ['test.fastq.gz'],
            project_id: 'proj_123',
            project_name: 'ignored_name'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toContain('--project-id');
      expect(command).toContain('proj_123');
      expect(command).not.toContain('--project-name');
      expect(command).not.toContain('ignored_name');
    });
  });

  describe('Cell Ranger Multi Analysis', () => {
    it('should build Cell Ranger multi command correctly', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'create_cellranger_multi_analysis',
          arguments: {
            analysis_name: 'multi_test',
            csv_path: '/path/to/config.csv',
            project_id: 'project_456',
            description: 'Test multi analysis',
            product_version: '9.0.1'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandInOrder(command,
        'analyses', 'create', 'cellranger', 'multi',
        '--analysis-name', 'multi_test',
        '--csv', '/path/to/config.csv',
        '--project-id', 'project_456',
        '--description', 'Test multi analysis',
        '--product-version', '9.0.1'
      );
    });
  });

  describe('Cell Ranger Aggr Analysis', () => {
    it('should build Cell Ranger aggr command correctly', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'create_cellranger_aggr_analysis',
          arguments: {
            analysis_name: 'aggr_test',
            csv_path: '/path/to/aggr.csv',
            project_id: 'project_789',
            normalize: 'mapped'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandContains(command,
        'analyses', 'create', 'cellranger', 'aggr',
        '--analysis-name', 'aggr_test',
        '--csv', '/path/to/aggr.csv',
        '--project-id', 'project_789',
        '--normalize', 'mapped'
      );
    });
  });

  describe('Upload Commands', () => {
    it('should build FASTQ upload command correctly', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'upload_fastqs',
          arguments: {
            project_id: 'project_789',
            file_path: '/data/fastqs/'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandInOrder(command,
        'fastqs', 'upload',
        '--project-id', 'project_789',
        '/data/fastqs/',
        '--assumeyes'
      );
    });

    it('should build project file upload command correctly', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'upload_project_file',
          arguments: {
            project_id: 'project_123',
            file_path: '/data/reference.csv'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandContains(command,
        'files', 'upload',
        '--project-id', 'project_123',
        '/data/reference.csv',
        '--assumeyes'
      );
    });
  });

  describe('List Commands', () => {
    it('should not include --assumeyes for list commands', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'list_projects',
          arguments: {}
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toEqual(['projects', 'list']);
      expect(command).not.toContain('--assumeyes');
    });

    it('should handle list with filter parameters', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'list_analyses',
          arguments: {
            project_id: 'project_123'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      // list_analyses uses positional argument, not --project-id flag
      expect(command).toEqual(['analyses', 'list', 'project_123']);
      expect(command).not.toContain('--assumeyes');
    });
  });

  describe('Auth Commands', () => {
    it('should build simple auth verify command', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'verify_auth',
          arguments: {}
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toEqual(['auth', 'verify']);
    });
  });

  describe('Special Cases', () => {
    it('should handle empty fastqs array', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      // The tool currently accepts empty fastqs array, even though it might not be valid
      await toolHandler({
        params: {
          name: 'create_cellranger_count_analysis',
          arguments: {
            analysis_name: 'test',
            transcriptome: 'GRCh38',
            fastqs: [],
            project_id: 'proj_123'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      // Should not include --fastqs if array is empty
      expect(command).toContain('--analysis-name');
      expect(command).toContain('test');
      expect(command).toContain('--transcriptome');
      expect(command).toContain('GRCh38');
      expect(command).toContain('--project-id');
      expect(command).toContain('proj_123');
      expect(command).not.toContain('--fastqs');
    });

    it('should handle special characters in parameters', async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: 'create_cellranger_count_analysis',
          arguments: {
            analysis_name: 'test with spaces & special!',
            transcriptome: 'GRCh38',
            fastqs: ['file with spaces.fastq.gz'],
            project_id: 'proj_123'
          }
        }
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toContain('test with spaces & special!');
      expect(command).toContain('file with spaces.fastq.gz');
    });
  });
});