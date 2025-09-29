/**
 * Integration tests for tool registration and error handling.
 * Command building is tested in command-builder.test.ts
 * Response transformation is tested in response-handler.test.ts
 */

import { jest } from '@jest/globals';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { registerTools } from '../../src/tools';
import { TOOL_DEFINITIONS } from '../../src/tool-definitions';
import * as txgCliManager from '../../src/txg-cli-manager';

describe('Tools Integration Tests', () => {
  let server: Server;
  let mockRunCommand: jest.MockedFunction<typeof txgCliManager.txgCli.runCommand>;
  let toolHandler: any;
  let listHandler: any;

  beforeEach(() => {
    process.env.ACCESS_TOKEN = 'test_token';
    process.env.NODE_ENV = 'test';

    server = new Server(
      { name: 'test-server', version: '1.0.0' },
      { capabilities: { tools: {}, prompts: {} } }
    );

    // Capture handlers when they're registered
    server.setRequestHandler = jest.fn((schema: any, handler: any) => {
      if (schema === CallToolRequestSchema) {
        toolHandler = handler;
      }
      return undefined as any;
    });

    // Set up the list handler
    listHandler = async () => ({
      tools: TOOL_DEFINITIONS
    });

    registerTools(server);

    mockRunCommand = jest.spyOn(txgCliManager.txgCli, 'runCommand').mockImplementation(
      async () => ({
        stdout: '',
        stderr: '',
        exitCode: 0,
        fullCommand: ''
      })
    ) as jest.MockedFunction<typeof txgCliManager.txgCli.runCommand>;
  });

  afterEach(() => {
    delete process.env.ACCESS_TOKEN;
    delete process.env.NODE_ENV;
    jest.restoreAllMocks();
  });

  describe('Tool Registration', () => {
    it('should register all tools with proper schema', async () => {
      const result = await listHandler({ params: {} } as any);

      expect(result.tools).toBeInstanceOf(Array);
      expect(result.tools.length).toBeGreaterThanOrEqual(25);

      // Verify each tool has required schema properties
      for (const tool of result.tools) {
        expect(tool.name).toBeTruthy();
        expect(tool.description).toBeTruthy();
        expect(tool.inputSchema).toBeTruthy();
        expect(tool.inputSchema.type).toBe('object');
        expect(tool.inputSchema.properties).toBeDefined();

        // Check for required fields if specified
        if (tool.inputSchema.required) {
          expect(tool.inputSchema.required).toBeInstanceOf(Array);
        }
      }

      // Spot check a few critical tools exist
      const toolNames = result.tools.map((t: any) => t.name);
      expect(toolNames).toContain('verify_auth');
      expect(toolNames).toContain('create_cellranger_count_analysis');
      expect(toolNames).toContain('list_projects');
    });
  });

  describe('Error Handling', () => {
    it('should reject invalid tool name', async () => {
      await expect(toolHandler({
        params: {
          name: 'invalid_tool_name',
          arguments: {}
        }
      } as any)).rejects.toThrow();
    });

    it('should validate required parameters', async () => {
      await expect(toolHandler({
        params: {
          name: 'create_cellranger_count_analysis',
          arguments: {
            // Missing required parameters: transcriptome, fastqs
            analysis_name: 'test'
          }
        }
      } as any)).rejects.toThrow();
    });

    it('should propagate CLI execution errors', async () => {
      mockRunCommand.mockRejectedValue(new Error('Execution failed'));

      await expect(toolHandler({
        params: {
          name: 'verify_auth',
          arguments: {}
        }
      } as any)).rejects.toThrow('Execution failed');
    });
  });

  describe('Concurrent Execution', () => {
    it('should handle multiple tool calls in parallel', async () => {
      mockRunCommand.mockResolvedValue({
        stdout: 'success',
        stderr: '',
        exitCode: 0,
        fullCommand: 'txg test'
      });

      // Execute multiple tools in parallel
      const results = await Promise.all([
        toolHandler({ params: { name: 'verify_auth', arguments: {} } } as any),
        toolHandler({ params: { name: 'get_tool_version', arguments: {} } } as any),
        toolHandler({ params: { name: 'list_projects', arguments: {} } } as any)
      ]);

      expect(results).toHaveLength(3);
      expect(mockRunCommand).toHaveBeenCalledTimes(3);

      // All should return valid responses
      for (const result of results) {
        expect(result.content).toBeDefined();
        expect(result.content[0].type).toBe('text');
      }
    });
  });
});