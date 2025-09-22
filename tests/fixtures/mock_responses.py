"""Mock responses for TXG CLI commands used in testing."""

# Successful auth verification
AUTH_SUCCESS = (
    "User authenticated successfully\nemail: user@example.com",
    "",
    0,
    "txg auth verify"
)

# Failed auth verification
AUTH_FAILURE = (
    "",
    "Error: Authentication failed. Token is invalid or expired.",
    1,
    "txg auth verify"
)

# Successful analysis creation
ANALYSIS_CREATED = (
    """Creating analysis...
Analysis created successfully
Analysis ID: analysis_12345
Project ID: project_67890
Status: PENDING""",
    "",
    0,
    "txg analyses create cellranger count --analysis-name test --transcriptome GRCh38"
)

# Version check
VERSION_INFO = (
    "txg version 1.2.3",
    "",
    0,
    "txg --version"
)

# List projects success
PROJECTS_LIST = (
    """[
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
]""",
    "",
    0,
    "txg projects list"
)

# Empty list
EMPTY_LIST = (
    "[]",
    "",
    0,
    "txg projects list"
)

# Command error
INVALID_COMMAND = (
    "",
    "Error: Invalid command or missing parameters",
    2,
    "txg invalid command"
)