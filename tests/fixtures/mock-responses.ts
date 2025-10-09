/**
 * Mock responses for TXG CLI commands used in testing.
 */

export interface CommandResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  fullCommand: string;
  inProgress: boolean;
}

// Successful auth verification
export const AUTH_SUCCESS: CommandResult = {
  stdout: "User authenticated successfully\nemail: user@example.com",
  stderr: "",
  exitCode: 0,
  fullCommand: "txg auth verify",
  inProgress: false,
};

// Failed auth verification
export const AUTH_FAILURE: CommandResult = {
  stdout: "",
  stderr: "Error: Authentication failed. Token is invalid or expired.",
  exitCode: 1,
  fullCommand: "txg auth verify",
  inProgress: false,
};

// Successful analysis creation
export const ANALYSIS_CREATED: CommandResult = {
  stdout: `Creating analysis...
Analysis created successfully
Analysis ID: analysis_12345
Project ID: project_67890
Status: PENDING`,
  stderr: "",
  exitCode: 0,
  fullCommand:
    "txg analyses create cellranger count --analysis-name test --transcriptome GRCh38",
  inProgress: false,
};

// Version check
export const VERSION_INFO: CommandResult = {
  stdout: "txg version 1.2.3",
  stderr: "",
  exitCode: 0,
  fullCommand: "txg --version",
  inProgress: false,
};

// List projects success
export const PROJECTS_LIST: CommandResult = {
  stdout: `[
  {
    "id": "project_123",
    "name": "Test Project",
    "description": "A test project",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "project_456",
    "name": "Another Project",
    "description": null,
    "created_at": "2024-01-02T00:00:00Z"
  }
]`,
  stderr: "",
  exitCode: 0,
  fullCommand: "txg projects list",
  inProgress: false,
};

// Empty list
export const EMPTY_LIST: CommandResult = {
  stdout: "[]",
  stderr: "",
  exitCode: 0,
  fullCommand: "txg projects list",
  inProgress: false,
};

// Command error
export const INVALID_COMMAND: CommandResult = {
  stdout: "",
  stderr: "Error: Invalid command or missing parameters",
  exitCode: 2,
  fullCommand: "txg invalid command",
  inProgress: false,
};

// Warning with success
export const SUCCESS_WITH_WARNING: CommandResult = {
  stdout: "Operation completed",
  stderr: "Warning: This is a warning message",
  exitCode: 0,
  fullCommand: "txg some command",
  inProgress: false,
};

// Multi-line output
export const MULTILINE_OUTPUT: CommandResult = {
  stdout: "Line 1\nLine 2\nLine 3\nLine 4",
  stderr: "",
  exitCode: 0,
  fullCommand: "txg test",
  inProgress: false,
};

// Special characters
export const SPECIAL_CHARS_OUTPUT: CommandResult = {
  stdout: "Result with \"quotes\" and 'apostrophes' and $pecial ch@rs!",
  stderr: "",
  exitCode: 0,
  fullCommand: "txg test",
  inProgress: false,
};
