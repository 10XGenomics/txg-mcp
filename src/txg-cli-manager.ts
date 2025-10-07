import { spawn } from "child_process";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";
import { fileURLToPath } from "url";

export interface CommandResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  fullCommand: string;
}

class TxgCliManager {
  private txgPath: string;
  private readonly platform: string;
  private readonly packageDir: string;
  private readonly accessToken: string | undefined;

  constructor() {
    this.platform = this.getPlatform();
    // Get directory of current module and go up to package root
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    // Go up from build/server/txg-cli-manager.js to package root
    this.packageDir = path.join(__dirname, "..");
    this.accessToken = process.env.ACCESS_TOKEN;
    this.txgPath = this.findBundledBinary();
  }

  private getPlatform(): string {
    const system = os.platform();

    // Map Node.js platform names to our directory names
    let platform: string;
    if (system === "darwin") {
      platform = "darwin";
    } else if (system === "linux") {
      platform = "linux";
    } else if (system === "win32") {
      platform = "windows";
    } else {
      throw new Error(`Unsupported operating system: ${system}`);
    }

    return platform;
  }

  private findBundledBinary(): string {
    // Skip binary check in test environment
    if (process.env.NODE_ENV === "test") {
      return "mock-txg-binary";
    }

    // Construct executable name based on platform
    const exeName = this.platform === "windows" ? "txg.exe" : "txg";

    // Build path to binary
    const binaryPath = path.join(
      this.packageDir,
      "bin",
      this.platform,
      exeName,
    );

    // Verify the binary exists
    if (!fs.existsSync(binaryPath)) {
      throw new Error(`txg binary not found at ${binaryPath}`);
    }

    // Ensure it's executable on Unix systems
    if (this.platform !== "windows") {
      try {
        fs.chmodSync(binaryPath, 0o755);
      } catch (_) {
        // Ignore chmod errors, binary might already be executable
      }
    }

    return binaryPath;
  }

  async runCommand(
    args: string[],
    timeout: number = 600000,
  ): Promise<CommandResult> {
    // In test mode, return mock result
    if (process.env.NODE_ENV === "test") {
      return Promise.resolve({
        stdout: "",
        stderr: "",
        exitCode: 0,
        fullCommand: `mock-txg ${args.join(" ")}`,
      });
    }

    return new Promise((resolve, reject) => {
      // Build full command array with access token if available
      const fullArgs = [...args];
      if (this.accessToken) {
        fullArgs.push("--access-token", this.accessToken);
      }

      fullArgs.push("--tags", "mcpb");

      const fullCommand = `${this.txgPath} ${fullArgs.join(" ")}`;

      const child = spawn(this.txgPath, fullArgs, {
        timeout: timeout,
      });

      let stdout = "";
      let stderr = "";
      let timedOut = false;

      // Set timeout handler
      const timeoutId = setTimeout(() => {
        timedOut = true;
        child.kill();
        reject(
          new Error(`Command timed out after ${timeout}ms: ${fullCommand}`),
        );
      }, timeout);

      child.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      child.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      child.on("error", (error) => {
        clearTimeout(timeoutId);
        reject(new Error(`Failed to run command: ${error.message}`));
      });

      child.on("close", (code) => {
        clearTimeout(timeoutId);
        if (!timedOut) {
          resolve({
            stdout: stdout.trim(),
            stderr: stderr.trim(),
            exitCode: code || 0,
            fullCommand,
          });
        }
      });
    });
  }
}

export const txgCli = new TxgCliManager();
