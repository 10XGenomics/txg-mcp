/**
 * Tests for command building from tool parameters.
 */

import { jest } from "@jest/globals";
import { registerTools } from "../../src/tools.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import * as txgCliManager from "../../src/txg-cli-manager.js";
import {
  assertCommandContains,
  assertCommandInOrder,
} from "../fixtures/test-helpers.js";

// We use a dummy response for all tests since we're only testing
// the command building logic, not the response handling
const DUMMY_RESPONSE = {
  stdout: "",
  stderr: "",
  exitCode: 0,
  fullCommand: "not-relevant-for-these-tests",
  inProgress: false,
};

describe("Command Building Tests", () => {
  // These tests verify that the tool handlers in tools.ts correctly
  // transform MCP tool parameters into CLI command arguments.
  // We spy on txgCli.runCommand to capture what commands would be executed.

  let server: Server;
  let mockRunCommand: jest.MockedFunction<
    typeof txgCliManager.txgCli.runCommand
  >;
  let toolHandler: any;

  beforeEach(() => {
    server = new Server(
      { name: "test-server", version: "1.0.0" },
      { capabilities: { tools: {}, prompts: {} } },
    );

    // Capture the handler when it's registered
    const originalSetRequestHandler = server.setRequestHandler.bind(server);
    server.setRequestHandler = function (schema: any, handler: any) {
      if (schema === CallToolRequestSchema) {
        toolHandler = handler;
      }
      return originalSetRequestHandler(schema, handler);
    };

    // Mock the runCommand method
    mockRunCommand = jest
      .spyOn(txgCliManager.txgCli, "runCommand")
      .mockImplementation(async (args: string[]) => {
        return {
          stdout: "",
          stderr: "",
          exitCode: 0,
          fullCommand: `txg ${args.join(" ")}`,
          inProgress: false,
        };
      }) as jest.MockedFunction<typeof txgCliManager.txgCli.runCommand>;

    registerTools(server);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe("Cell Ranger Count Analysis", () => {
    it("should transform MCP parameters to CLI command correctly", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      // Call the tool with MCP-style parameters
      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test_analysis",
            transcriptome: "GRCh38",
            fastqs: ["sample_S1_L001_R1_001.fastq.gz"],
            project_id: "project_123",
          },
        },
      } as any);

      // Verify the command that would be sent to the CLI
      expect(mockRunCommand).toHaveBeenCalledTimes(1);
      const command = mockRunCommand.mock.calls[0][0];

      // The tool should build this exact command structure
      expect(command.slice(0, 7)).toEqual([
        "analyses",
        "create",
        "cellranger",
        "count",
        "--product-version",
        "latest",
        "--analysis-name",
      ]);
      expect(command[7]).toBe("test_analysis");

      // Verify all required parameters are correctly formatted
      assertCommandContains(
        command,
        "--transcriptome",
        "GRCh38",
        "--fastqs",
        "sample_S1_L001_R1_001.fastq.gz",
        "--project-id",
        "project_123",
        "--wait-completion=false",
      );
    });

    it("should handle optional parameters correctly", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test_analysis",
            transcriptome: "GRCh38",
            fastqs: ["sample1.fastq.gz", "sample2.fastq.gz"],
            project_name: "new_project",
            expect_cells: 5000,
            chemistry: "SC3Pv3",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandContains(
        command,
        "--project-name",
        "new_project",
        "--expect-cells",
        "5000",
        "--chemistry",
        "SC3Pv3",
      );

      // Should have two fastq entries
      const fastqIndices = command.reduce((indices: number[], item, index) => {
        if (item === "--fastqs") {
          indices.push(index);
        }
        return indices;
      }, []);
      expect(fastqIndices.length).toBe(2);
    });

    it("should prefer project_id over project_name when both provided", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test",
            transcriptome: "GRCh38",
            fastqs: ["test.fastq.gz"],
            project_id: "proj_123",
            project_name: "ignored_name",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toContain("--project-id");
      expect(command).toContain("proj_123");
      expect(command).not.toContain("--project-name");
      expect(command).not.toContain("ignored_name");
    });

    it("should handle new optional parameters (force_cells, create_bam, nosecondary, r1_length, r2_length)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test_analysis",
            transcriptome: "GRCh38",
            fastqs: ["sample.fastq.gz"],
            project_id: "project_123",
            force_cells: 5000,
            create_bam: false,
            nosecondary: true,
            r1_length: 28,
            r2_length: 91,
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandContains(
        command,
        "--force-cells",
        "5000",
        "--create-bam=false",
        "--nosecondary",
        "--r1-length",
        "28",
        "--r2-length",
        "91",
      );

      // Should not contain expect_cells since force_cells is used
      expect(command).not.toContain("--expect-cells");
    });

    it("should handle create_bam=true", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test",
            transcriptome: "GRCh38",
            fastqs: ["test.fastq.gz"],
            project_id: "proj_123",
            create_bam: true,
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--create-bam=true");
    });
  });

  describe("Cell Ranger Multi Analysis", () => {
    it("should build Cell Ranger multi command correctly", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_multi_analysis",
          arguments: {
            analysis_name: "multi_test",
            csv_path: "/path/to/config.csv",
            project_id: "project_456",
            description: "Test multi analysis",
            product_version: "9.0.1",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandInOrder(
        command,
        "analyses",
        "create",
        "cellranger",
        "multi",
        "--product-version",
        "latest",
        "--analysis-name",
        "multi_test",
        "--csv",
        "/path/to/config.csv",
        "--project-id",
        "project_456",
        "--description",
        "Test multi analysis",
      );
    });
  });

  describe("Cell Ranger Aggr Analysis", () => {
    it("should build Cell Ranger aggr command correctly", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_aggr_analysis",
          arguments: {
            analysis_name: "aggr_test",
            csv_path: "/path/to/aggr.csv",
            project_id: "project_789",
            normalize: "mapped",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandContains(
        command,
        "analyses",
        "create",
        "cellranger",
        "aggr",
        "--analysis-name",
        "aggr_test",
        "--csv",
        "/path/to/aggr.csv",
        "--project-id",
        "project_789",
        "--normalize",
        "mapped",
      );
    });
  });

  describe("Upload Commands", () => {
    it("should build FASTQ upload command correctly", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "upload_fastqs",
          arguments: {
            project_id: "project_789",
            file_path: "/data/fastqs/",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandInOrder(
        command,
        "fastqs",
        "upload",
        "--project-id",
        "project_789",
        "/data/fastqs/",
      );
    });

    it("should build project file upload command correctly", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "upload_project_file",
          arguments: {
            project_id: "project_123",
            file_path: "/data/reference.csv",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      assertCommandContains(
        command,
        "files",
        "upload",
        "--project-id",
        "project_123",
        "/data/reference.csv",
      );
    });
  });

  describe("List Commands", () => {
    it("should run projects list command", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "list_projects",
          arguments: {},
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toEqual(["projects", "list"]);
    });

    it("should handle list with filter parameters", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "list_analyses",
          arguments: {
            project_id: "project_123",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      // list_analyses uses positional argument, not --project-id flag
      expect(command).toEqual(["analyses", "list", "project_123"]);
    });
  });

  describe("Auth Commands", () => {
    it("should build simple auth verify command", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "verify_auth",
          arguments: {},
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toEqual(["auth", "verify"]);
    });
  });

  describe("Payment Acceptance", () => {
    it("should include --accept-payment=false when accept_payment is omitted (count)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test_analysis",
            transcriptome: "GRCh38",
            fastqs: ["sample.fastq.gz"],
            project_id: "project_123",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=false");
      expect(command).not.toContain("--accept-payment=true");
    });

    it("should include --accept-payment=false when accept_payment is 'false' (count)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test_analysis",
            transcriptome: "GRCh38",
            fastqs: ["sample.fastq.gz"],
            project_id: "project_123",
            accept_payment: "false",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=false");
      expect(command).not.toContain("--accept-payment=true");
    });

    it("should include --accept-payment=true when accept_payment is 'true' (count)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test_analysis",
            transcriptome: "GRCh38",
            fastqs: ["sample.fastq.gz"],
            project_id: "project_123",
            accept_payment: "true",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=true");
      expect(command).not.toContain("--accept-payment=false");
    });

    it("should include --accept-payment=false when accept_payment is omitted (multi)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_multi_analysis",
          arguments: {
            analysis_name: "multi_test",
            csv_path: "/path/to/config.csv",
            project_id: "project_456",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=false");
      expect(command).not.toContain("--accept-payment=true");
    });

    it("should include --accept-payment=true when accept_payment is 'true' (multi)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_multi_analysis",
          arguments: {
            analysis_name: "multi_test",
            csv_path: "/path/to/config.csv",
            project_id: "project_456",
            accept_payment: "true",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=true");
      expect(command).not.toContain("--accept-payment=false");
    });

    it("should include --accept-payment=false when accept_payment is omitted (aggr)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_aggr_analysis",
          arguments: {
            analysis_name: "aggr_test",
            csv_path: "/path/to/aggr.csv",
            project_id: "project_789",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=false");
      expect(command).not.toContain("--accept-payment=true");
    });

    it("should include --accept-payment=true when accept_payment is 'true' (aggr)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_aggr_analysis",
          arguments: {
            analysis_name: "aggr_test",
            csv_path: "/path/to/aggr.csv",
            project_id: "project_789",
            accept_payment: "true",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=true");
      expect(command).not.toContain("--accept-payment=false");
    });

    it("should handle any other string value as false (aggr)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_aggr_analysis",
          arguments: {
            analysis_name: "aggr_test",
            csv_path: "/path/to/aggr.csv",
            project_id: "project_789",
            accept_payment: "yes",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=false");
      expect(command).not.toContain("--accept-payment=true");
    });

    it("should handle boolean true (count)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test_analysis",
            transcriptome: "GRCh38",
            fastqs: ["sample.fastq.gz"],
            project_id: "project_123",
            accept_payment: true,
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=true");
      expect(command).not.toContain("--accept-payment=false");
    });

    it("should handle boolean false (multi)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_multi_analysis",
          arguments: {
            analysis_name: "multi_test",
            csv_path: "/path/to/config.csv",
            project_id: "project_456",
            accept_payment: false,
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];
      expect(command).toContain("--accept-payment=false");
      expect(command).not.toContain("--accept-payment=true");
    });
  });

  describe("Special Cases", () => {
    it("should handle empty fastqs array", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      // The tool currently accepts empty fastqs array, even though it might not be valid
      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test",
            transcriptome: "GRCh38",
            fastqs: [],
            project_id: "proj_123",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      // Should not include --fastqs if array is empty
      expect(command).toContain("--analysis-name");
      expect(command).toContain("test");
      expect(command).toContain("--transcriptome");
      expect(command).toContain("GRCh38");
      expect(command).toContain("--project-id");
      expect(command).toContain("proj_123");
      expect(command).not.toContain("--fastqs");
    });

    it("should handle special characters in parameters", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test with spaces & special!",
            transcriptome: "GRCh38",
            fastqs: ["file with spaces.fastq.gz"],
            project_id: "proj_123",
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      expect(command).toContain("test with spaces & special!");
      expect(command).toContain("file with spaces.fastq.gz");
    });

    it("should handle numeric parameters passed as strings (LLM defensive)", async () => {
      mockRunCommand.mockResolvedValue(DUMMY_RESPONSE);

      await toolHandler({
        params: {
          name: "create_cellranger_count_analysis",
          arguments: {
            analysis_name: "test",
            transcriptome: "GRCh38",
            fastqs: ["test.fastq.gz"],
            project_id: "proj_123",
            expect_cells: "1000", // String instead of number
            r1_length: "28", // String instead of number
            r2_length: "91", // String instead of number
          },
        },
      } as any);

      const command = mockRunCommand.mock.calls[0][0];

      // Should correctly convert strings to numbers
      assertCommandContains(
        command,
        "--expect-cells",
        "1000",
        "--r1-length",
        "28",
        "--r2-length",
        "91",
      );
    });
  });
});
