/**
 * Tests for response transformation and error handling.
 */

import type { Response } from "../../src/middleware.js";
import { toResponse, toAnalysisResponse } from "../../src/middleware.js";
import {
  VERSION_INFO,
  AUTH_FAILURE,
  ANALYSIS_CREATED,
  PROJECTS_LIST,
  EMPTY_LIST,
  SUCCESS_WITH_WARNING,
  MULTILINE_OUTPUT,
  SPECIAL_CHARS_OUTPUT,
} from "../fixtures/mock-responses.js";

describe("Response Handling Tests", () => {
  describe("toResponse", () => {
    it("should handle successful response transformation", () => {
      const result = toResponse(VERSION_INFO) as Response;

      expect(result.status).toBe("success");
      expect(result.content).toBe("txg version 1.2.3");
      expect(result.error).toBe("");
      expect(result.returncode).toBe(0);
      expect(result.fullCommand).toBe("txg --version");
    });

    it("should handle failed response transformation", () => {
      const result = toResponse(AUTH_FAILURE) as Response;

      expect(result.status).toBe("error");
      expect(result.content).toBe("");
      expect(result.error).toContain("Authentication failed");
      expect(result.returncode).toBe(1);
    });

    it("should handle response with stderr warning but success code", () => {
      const result = toResponse(SUCCESS_WITH_WARNING) as Response;

      expect(result.status).toBe("success");
      // On success, error should be empty even if stderr has content
      expect(result.content).toBe("Operation completed");
      expect(result.error).toBe("");
      expect(result.returncode).toBe(0);
    });

    it("should preserve JSON response formatting", () => {
      const result = toResponse(PROJECTS_LIST) as Response;

      expect(result.status).toBe("success");
      expect(result.content).toContain('"id": "project_123"');
      expect(result.content).toContain('"name": "Test Project"');
      expect(result.error).toBe("");
    });

    it("should handle empty list responses", () => {
      const result = toResponse(EMPTY_LIST) as Response;

      expect(result.status).toBe("success");
      expect(result.content).toBe("[]");
      expect(result.error).toBe("");
      expect(result.returncode).toBe(0);
    });

    it("should preserve multiline output", () => {
      const result = toResponse(MULTILINE_OUTPUT) as Response;

      expect(result.status).toBe("success");
      expect(result.content).toBe("Line 1\nLine 2\nLine 3\nLine 4");
      expect(result.content.split("\n").length).toBe(4);
    });

    it("should preserve special characters", () => {
      const result = toResponse(SPECIAL_CHARS_OUTPUT) as Response;

      expect(result.status).toBe("success");
      expect(result.content).toContain('"quotes"');
      expect(result.content).toContain("'apostrophes'");
      expect(result.content).toContain("$pecial ch@rs!");
    });

    it("should handle different error codes correctly", () => {
      const errorCases = [
        { exitCode: 1, errorMsg: "General error" },
        { exitCode: 2, errorMsg: "Invalid command" },
        { exitCode: 127, errorMsg: "Command not found" },
        { exitCode: 255, errorMsg: "Unknown error" },
      ];

      for (const { exitCode, errorMsg } of errorCases) {
        const result = toResponse({
          stdout: "",
          stderr: errorMsg,
          exitCode,
          fullCommand: "txg test",
          inProgress: false,
        }) as Response;

        expect(result.status).toBe("error");
        expect(result.returncode).toBe(exitCode);
        expect(result.error).toBe(errorMsg);
        expect(result.content).toBe("");
      }
    });
  });

  describe("toAnalysisResponse", () => {
    it("should add extra fields for successful analysis creation", () => {
      const result = toAnalysisResponse(ANALYSIS_CREATED) as Response;

      expect(result.status).toBe("success");
      expect(result.message).toContain("Analysis started successfully");
      expect(result.next_steps).toBeDefined();
      expect(result.next_steps).toContain("get_analysis_details");
      expect(result.next_steps).toContain("email notification");
    });

    it("should not add extra fields for failed analysis creation", () => {
      const failedResult = {
        stdout: "",
        stderr: "Error: Invalid parameters",
        exitCode: 1,
        fullCommand: "txg analyses create",
        inProgress: false,
      };

      const result = toAnalysisResponse(failedResult) as Response;

      expect(result.status).toBe("error");
      expect(result.message).toBeUndefined();
      expect(result.next_steps).toBeUndefined();
      expect(result.error).toBe("Error: Invalid parameters");
    });

    it("should preserve all base response fields", () => {
      const result = toAnalysisResponse(ANALYSIS_CREATED) as Response;

      expect(result.content).toContain("Analysis created successfully");
      expect(result.error).toBe("");
      expect(result.returncode).toBe(0);
      expect(result.fullCommand).toBeDefined();
    });
  });

  describe("Security", () => {
    it("should preserve fullCommand as-is (access token now passed via env var)", () => {
      const result = toResponse({
        stdout: "Success",
        stderr: "",
        exitCode: 0,
        fullCommand: "txg analyses list",
        inProgress: false,
      }) as Response;

      expect(result.status).toBe("success");
      expect(result.fullCommand).toBe("txg analyses list");
    });

    it("should handle version command", () => {
      const result = toResponse({
        stdout: "Success",
        stderr: "",
        exitCode: 0,
        fullCommand: "txg --version",
        inProgress: false,
      }) as Response;

      expect(result.status).toBe("success");
      expect(result.fullCommand).toBe("txg --version");
    });

    it("should preserve fullCommand for failed commands", () => {
      const result = toResponse({
        stdout: "",
        stderr: "Error",
        exitCode: 1,
        fullCommand: "txg analyses create --project-id foo",
        inProgress: false,
      }) as Response;

      expect(result.status).toBe("error");
      expect(result.fullCommand).toBe("txg analyses create --project-id foo");
    });
  });

  describe("Edge Cases", () => {
    it("should handle null/undefined values gracefully", () => {
      const result = toResponse({
        stdout: "",
        stderr: "",
        exitCode: 0,
        fullCommand: "txg test",
        inProgress: false,
      }) as Response;

      expect(result.status).toBe("success");
      expect(result.content).toBe("");
      expect(result.error).toBe("");
    });

    it("should handle very long output", () => {
      const longOutput = "x".repeat(10000);
      const result = toResponse({
        stdout: longOutput,
        stderr: "",
        exitCode: 0,
        fullCommand: "txg test",
        inProgress: false,
      }) as Response;

      expect(result.status).toBe("success");
      expect(result.content).toBe(longOutput);
      expect(result.content.length).toBe(10000);
    });

    it("should handle mixed success indicators", () => {
      // stdout with error message but success code
      const result1 = toResponse({
        stdout: "Error: Something happened but it's okay",
        stderr: "",
        exitCode: 0,
        fullCommand: "txg test",
        inProgress: false,
      }) as Response;

      expect(result1.status).toBe("success");
      expect(result1.content).toContain("Error:");

      // stderr with info message but failure code
      const result2 = toResponse({
        stdout: "",
        stderr: "Info: Process failed",
        exitCode: 1,
        fullCommand: "txg test",
        inProgress: false,
      }) as Response;

      expect(result2.status).toBe("error");
      expect(result2.error).toContain("Info:");
    });
  });
});
