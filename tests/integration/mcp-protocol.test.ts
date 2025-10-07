/**
 * Tests for MCP protocol compliance.
 */

import type { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Readable, Writable } from "stream";

interface JsonRpcRequest {
  jsonrpc: "2.0";
  method: string;
  params?: any;
  id?: number | string;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
  id: number | string;
}

class TestTransport {
  private input: Readable;
  private output: Writable;
  private responseBuffer: string = "";
  private responsePromises: Map<
    number | string,
    (response: JsonRpcResponse) => void
  > = new Map();

  constructor() {
    this.input = new Readable({
      read() {},
    });
    this.output = new Writable({
      write: (chunk, encoding, callback) => {
        this.responseBuffer += chunk.toString();
        const lines = this.responseBuffer.split("\n");
        this.responseBuffer = lines.pop() || "";

        for (const line of lines) {
          if (line.trim()) {
            try {
              const response = JSON.parse(line);
              const resolver = this.responsePromises.get(response.id);
              if (resolver) {
                resolver(response);
                this.responsePromises.delete(response.id);
              }
            } catch (_) {
              // Ignore parse errors
            }
          }
        }
        callback();
      },
    });
  }

  async sendRequest(request: JsonRpcRequest): Promise<JsonRpcResponse> {
    return new Promise((resolve) => {
      if (request.id !== undefined) {
        this.responsePromises.set(request.id, resolve);
      }
      this.input.push(JSON.stringify(request) + "\n");
    });
  }

  getStreams() {
    return { input: this.input, output: this.output };
  }

  close() {
    this.input.destroy();
    this.output.destroy();
  }
}

describe("MCP Protocol Tests", () => {
  let transport: TestTransport;
  let server: Server;

  beforeEach(async () => {
    // Set up environment
    process.env.ACCESS_TOKEN = "test_token";
    process.env.NODE_ENV = "test";

    // Dynamically import to ensure NODE_ENV is set first
    const { createServer } = await import("../../src/index");

    server = createServer();

    // Create test transport
    transport = new TestTransport();
    const { input, output } = transport.getStreams();
    const stdioTransport = new StdioServerTransport(input, output);

    await server.connect(stdioTransport);
  });

  afterEach(async () => {
    if (transport) {
      transport.close();
    }
    if (server) {
      await server.close();
    }
    delete process.env.ACCESS_TOKEN;
    delete process.env.NODE_ENV;
  });

  describe("Initialization", () => {
    it("should handle initialize request correctly", async () => {
      const response = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "initialize",
        params: {
          protocolVersion: "0.1.0",
          capabilities: {},
          clientInfo: {
            name: "test-client",
            version: "1.0.0",
          },
        },
        id: 1,
      });

      expect(response.result).toBeDefined();
      expect(response.result.serverInfo).toBeDefined();
      expect(response.result.serverInfo.name).toBe("10x-genomics");
      expect(response.result.serverInfo.version).toBe("1.0.0");
      expect(response.result.capabilities).toBeDefined();
    });

    it("should handle initialized notification", async () => {
      // First initialize
      await transport.sendRequest({
        jsonrpc: "2.0",
        method: "initialize",
        params: {
          protocolVersion: "0.1.0",
          capabilities: {},
          clientInfo: {
            name: "test-client",
            version: "1.0.0",
          },
        },
        id: 1,
      });

      // Send initialized notification (no response expected, no id)
      // Just push to stream without waiting for response
      const { input } = transport.getStreams();
      input.push(
        JSON.stringify({
          jsonrpc: "2.0",
          method: "notifications/initialized",
          params: {},
        }) + "\n",
      );

      // Give server a moment to process the notification
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Server should be ready for next request
      const toolsResponse = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "tools/list",
        params: {},
        id: 2,
      });

      expect(toolsResponse.result).toBeDefined();
      expect(toolsResponse.result.tools).toBeDefined();
    }, 10000);
  });

  describe("Tools", () => {
    beforeEach(async () => {
      // Initialize connection
      await transport.sendRequest({
        jsonrpc: "2.0",
        method: "initialize",
        params: {
          protocolVersion: "0.1.0",
          capabilities: {},
          clientInfo: {
            name: "test-client",
            version: "1.0.0",
          },
        },
        id: 0,
      });
    });

    it("should list all available tools", async () => {
      const response = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "tools/list",
        params: {},
        id: 1,
      });

      expect(response.result).toBeDefined();
      expect(response.result.tools).toBeInstanceOf(Array);
      expect(response.result.tools.length).toBeGreaterThan(20);

      const toolNames = response.result.tools.map((t: any) => t.name);
      expect(toolNames).toContain("verify_auth");
      expect(toolNames).toContain("create_cellranger_count_analysis");
      expect(toolNames).toContain("list_projects");
      expect(toolNames).toContain("get_tool_version");
    });

    it("should have proper tool structure", async () => {
      const response = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "tools/list",
        params: {},
        id: 1,
      });

      for (const tool of response.result.tools) {
        expect(tool).toHaveProperty("name");
        expect(tool).toHaveProperty("description");
        expect(tool).toHaveProperty("inputSchema");
        expect(tool.inputSchema).toHaveProperty("type");
        expect(tool.inputSchema).toHaveProperty("properties");
      }
    });
  });

  describe("Prompts", () => {
    beforeEach(async () => {
      // Initialize connection
      await transport.sendRequest({
        jsonrpc: "2.0",
        method: "initialize",
        params: {
          protocolVersion: "0.1.0",
          capabilities: {},
          clientInfo: {
            name: "test-client",
            version: "1.0.0",
          },
        },
        id: 0,
      });
    });

    it("should list available prompts", async () => {
      const response = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "prompts/list",
        params: {},
        id: 1,
      });

      expect(response.result).toBeDefined();
      expect(response.result.prompts).toBeInstanceOf(Array);

      // const promptNames = response.result.prompts.map((p: any) => p.name);
      // expect(promptNames).toContain('confirm_analysis_parameters');
    });

    it("should have proper prompt structure", async () => {
      const response = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "prompts/list",
        params: {},
        id: 1,
      });

      for (const prompt of response.result.prompts) {
        expect(prompt).toHaveProperty("name");
        expect(prompt).toHaveProperty("description");
      }
    });
  });

  describe("Error Handling", () => {
    beforeEach(async () => {
      await transport.sendRequest({
        jsonrpc: "2.0",
        method: "initialize",
        params: {
          protocolVersion: "0.1.0",
          capabilities: {},
          clientInfo: {
            name: "test-client",
            version: "1.0.0",
          },
        },
        id: 0,
      });
    });

    it("should handle invalid method", async () => {
      const response = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "invalid/method",
        params: {},
        id: 1,
      });

      expect(response.error).toBeDefined();
      expect(response.error?.code).toBeDefined();
      expect(response.error?.message).toBeDefined();
    });

    it("should handle malformed requests", async () => {
      const response = await transport.sendRequest({
        jsonrpc: "2.0",
        method: "tools/call",
        params: {
          // Missing required fields
        },
        id: 1,
      });

      expect(response.error).toBeDefined();
    });
  });

  describe("JSON-RPC Compliance", () => {
    it("should include jsonrpc version in all responses", async () => {
      const responses = [
        await transport.sendRequest({
          jsonrpc: "2.0",
          method: "initialize",
          params: {
            protocolVersion: "0.1.0",
            capabilities: {},
            clientInfo: { name: "test", version: "1.0.0" },
          },
          id: 1,
        }),
        await transport.sendRequest({
          jsonrpc: "2.0",
          method: "tools/list",
          params: {},
          id: 2,
        }),
        await transport.sendRequest({
          jsonrpc: "2.0",
          method: "prompts/list",
          params: {},
          id: 3,
        }),
      ];

      for (const response of responses) {
        expect(response.jsonrpc).toBe("2.0");
      }
    });

    it("should echo request id in responses", async () => {
      const testIds = [1, "test-id", 999];

      for (const id of testIds) {
        const response = await transport.sendRequest({
          jsonrpc: "2.0",
          method: "tools/list",
          params: {},
          id,
        });

        expect(response.id).toBe(id);
      }
    });
  });
});
