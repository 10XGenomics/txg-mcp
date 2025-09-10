/**
 * Type definitions for TXG MCP Server
 */
// Error types
export class TxgError extends Error {
    code;
    exitCode;
    constructor(message, code, exitCode) {
        super(message);
        this.code = code;
        this.exitCode = exitCode;
        this.name = 'TxgError';
    }
}
export class ValidationError extends TxgError {
    constructor(message) {
        super(message, 'VALIDATION_ERROR');
        this.name = 'ValidationError';
    }
}
export class CommandNotAllowedError extends TxgError {
    constructor(command) {
        super(`Command not allowed: ${command}`, 'COMMAND_NOT_ALLOWED');
        this.name = 'CommandNotAllowedError';
    }
}
export class ExecutionError extends TxgError {
    constructor(message, exitCode) {
        super(message, 'EXECUTION_ERROR', exitCode);
        this.name = 'ExecutionError';
    }
}
//# sourceMappingURL=index.js.map