#!/usr/bin/env node

/**
 * Query MCP server capabilities via JSON-RPC protocol.
 *
 * This script starts an MCP server as a subprocess and queries its capabilities
 * using the MCP JSON-RPC protocol over stdio. It retrieves tools, resources,
 * and prompts information and outputs them as a formatted JSON structure.
 */

import { spawn } from "child_process";
import { writeFileSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Send a JSON-RPC request to the process and get response
 */
function sendJsonRpc(process, method, params = null, id = 1) {
  return new Promise((resolve, reject) => {
    const request = {
      jsonrpc: "2.0",
      method: method,
      id: id,
    };

    if (params !== undefined) {
      request.params = params;
    }

    const requestStr = JSON.stringify(request) + "\n";

    // Set timeout for response
    const timeout = setTimeout(() => {
      reject(new Error(`Timeout waiting for response to ${method}`));
    }, 5000);

    // Collect response data
    let responseBuffer = "";

    const responseHandler = (data) => {
      responseBuffer += data.toString();

      // Try to parse complete JSON responses from buffer
      const lines = responseBuffer.split("\n");
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim();
        if (line) {
          try {
            const response = JSON.parse(line);
            if (response.id === id) {
              clearTimeout(timeout);
              process.stdout.removeListener("data", responseHandler);
              resolve(response);
              return;
            }
          } catch (_) {
            // Not a complete JSON yet, continue collecting
          }
        }
      }
      // Keep the last incomplete line in buffer
      responseBuffer = lines[lines.length - 1];
    };

    process.stdout.on("data", responseHandler);
    process.stdin.write(requestStr);
  });
}

/**
 * Send a notification (no response expected)
 */
function sendNotification(process, method, params) {
  const notification = {
    jsonrpc: "2.0",
    method: method,
  };

  if (params !== undefined) {
    notification.params = params;
  }

  const notificationStr = JSON.stringify(notification) + "\n";
  process.stdin.write(notificationStr);
}

/**
 * Query all capabilities from the MCP server
 */
async function queryCapabilities(serverPath, accessToken) {
  return new Promise((resolve, reject) => {
    // Start the server as a subprocess
    const env = { ...process.env };
    env.TXG_CLI_ACCESS_TOKEN = accessToken;

    const serverProcess = spawn("node", [serverPath], {
      env: env,
      stdio: ["pipe", "pipe", "pipe"],
    });

    serverProcess.on("error", (error) => {
      reject(new Error(`Failed to start server: ${error.message}`));
    });

    // Wait for server to be ready (looking for the "running" message on stderr)
    const waitForServer = new Promise((resolve) => {
      let stderrBuffer = "";
      const timeout = setTimeout(() => {
        // If timeout, assume server is ready anyway
        resolve();
      }, 2000);

      const stderrHandler = (data) => {
        stderrBuffer += data.toString();
        // Server outputs "10x Genomics MCP Server running..." to stderr
        if (
          stderrBuffer.includes("running") ||
          stderrBuffer.includes("Server")
        ) {
          clearTimeout(timeout);
          serverProcess.stderr.removeListener("data", stderrHandler);
          resolve();
        }
      };

      serverProcess.stderr.on("data", stderrHandler);
    });

    waitForServer.then(async () => {
      try {
        const capabilities = {};

        // Step 1: Send initialize request
        const initResponse = await sendJsonRpc(
          serverProcess,
          "initialize",
          {
            protocolVersion: "2024-11-05",
            capabilities: {},
            clientInfo: {
              name: "mcp-capabilities-generator",
              version: "1.0.0",
            },
          },
          1,
        );

        if (initResponse.result) {
          capabilities.server_info = initResponse.result.serverInfo || {};
          capabilities.protocol_version =
            initResponse.result.protocolVersion || "";
          capabilities.capabilities = initResponse.result.capabilities || {};
        }

        // Step 2: Send initialized notification
        sendNotification(serverProcess, "notifications/initialized");
        await new Promise((resolve) => setTimeout(resolve, 100));

        // Step 3: Get tools list
        try {
          const toolsResponse = await sendJsonRpc(
            serverProcess,
            "tools/list",
            {},
            2,
          );
          if (toolsResponse.result) {
            capabilities.tools = toolsResponse.result.tools || [];
          } else if (toolsResponse.error) {
            capabilities.tools = [];
            capabilities.tools_error = toolsResponse.error;
          }
        } catch (e) {
          capabilities.tools = [];
          capabilities.tools_error = e.message;
        }

        // Step 4: Get resources list
        try {
          const resourcesResponse = await sendJsonRpc(
            serverProcess,
            "resources/list",
            {},
            3,
          );
          if (resourcesResponse.result) {
            capabilities.resources = resourcesResponse.result.resources || [];
          } else if (resourcesResponse.error) {
            capabilities.resources = [];
            capabilities.resources_error = resourcesResponse.error;
          }
        } catch (e) {
          capabilities.resources = [];
          capabilities.resources_error = e.message;
        }

        // Step 5: Get prompts list
        try {
          const promptsResponse = await sendJsonRpc(
            serverProcess,
            "prompts/list",
            {},
            4,
          );
          if (promptsResponse.result) {
            capabilities.prompts = promptsResponse.result.prompts || [];
          } else if (promptsResponse.error) {
            capabilities.prompts = [];
            capabilities.prompts_error = promptsResponse.error;
          }
        } catch (e) {
          capabilities.prompts = [];
          capabilities.prompts_error = e.message;
        }

        resolve(capabilities);
      } catch (error) {
        reject(error);
      } finally {
        // Terminate the server gracefully
        serverProcess.kill("SIGTERM");

        // Force kill if it doesn't terminate in 5 seconds
        setTimeout(() => {
          if (!serverProcess.killed) {
            serverProcess.kill("SIGKILL");
          }
        }, 5000);
      }
    });
  });
}

/**
 * Main function
 */
async function main() {
  try {
    // Parse arguments
    const args = process.argv.slice(2);

    // Access token can come from argument or we'll use empty string (server can handle it)
    const accessToken = args[0] || "";
    const outputFile =
      args[1] ||
      join(dirname(__dirname), "reference", "mcp_capabilities_reference.json");

    // Validate server exists
    const serverPath = join(dirname(__dirname), "build", "server", "index.js");
    if (!existsSync(serverPath)) {
      console.error(`Error: Server not found at ${serverPath}`);
      console.error('Run "npm run build" first');
      process.exit(1);
    }

    console.log("ℹ Querying server capabilities...");

    // Query capabilities
    const capabilities = await queryCapabilities(serverPath, accessToken);

    // Count capabilities
    const toolsCount = capabilities.tools?.length || 0;
    const resourcesCount = capabilities.resources?.length || 0;
    const promptsCount = capabilities.prompts?.length || 0;

    // Ensure output directory exists
    const outputDir = dirname(outputFile);
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true });
    }

    // Write to file
    writeFileSync(outputFile, JSON.stringify(capabilities, null, 2));

    console.log(
      `✓ Successfully generated capabilities reference: ${outputFile}`,
    );
    console.log(
      `ℹ Found: ${toolsCount} tools, ${resourcesCount} resources, ${promptsCount} prompts`,
    );
  } catch (error) {
    console.error(`✗ Error querying capabilities: ${error.message}`);
    process.exit(1);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
