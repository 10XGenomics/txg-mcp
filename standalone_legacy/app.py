# app.py
# A simple Flask server to expose the TXG CLI to LLMs via MCP.

import subprocess
import json
import re
import inspect # Import the inspect module
from flask import Flask, request, jsonify

# --- CHANGE: Dynamically build the command allowlist ---
import tools # Import the tools module
from langchain_core.tools import BaseTool

def build_allowed_commands():
    """
    Inspects the 'tools' module to find all functions decorated with our
    custom @mcp_tool decorator and builds a set of allowed command prefixes.
    """
    allowed_set = set()
    # inspect.getmembers returns all members of an object (the tools module)
    for name, member in inspect.getmembers(tools):
        # We look for members that are LangChain tools
        if isinstance(member, BaseTool):
            # The original function is stored in the .func attribute
            original_func = member.func
            # Check if our custom attribute exists
            if hasattr(original_func, 'mcp_command_prefix'):
                allowed_set.add(original_func.mcp_command_prefix)
    return allowed_set

# Build the allowlist when the application starts
ALLOWED_COMMANDS = build_allowed_commands()
print("✅ Dynamically generated command allowlist:")
for cmd in sorted(list(ALLOWED_COMMANDS)):
    print(f"  - {cmd}")


app = Flask(__name__)
TXG_EXECUTABLE = "/usr/local/bin/txg"

def run_txg_command(command_parts):
    """Executes a TXG command securely using subprocess.Popen."""
    try:
        process = subprocess.Popen(
            command_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        output_lines = []
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            output_lines.append(line)
        
        process.stdout.close()
        return_code = process.wait()
        full_output = "".join(output_lines)
        return full_output, None, return_code

    except FileNotFoundError:
        return f"Error: '{TXG_EXECUTABLE}' not found. Is the path correct?", None, 1
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}", None, 1

@app.route('/run_command', methods=['POST'])
def handle_run_command():
    """
    Receives a command list, validates it against the dynamically generated
    allowlist, sanitizes it, executes it, and returns the result.
    """
    data = request.get_json()
    command_from_client = data.get('command')

    if not command_from_client or not isinstance(command_from_client, list):
        return jsonify({"error": "Invalid or missing 'command' in request payload."}), 400

    # --- Allowlist Validation (now using the dynamic set) ---
    is_allowed = False
    for allowed_cmd in ALLOWED_COMMANDS:
        if tuple(command_from_client[:len(allowed_cmd)]) == allowed_cmd:
            is_allowed = True
            break
    
    if not is_allowed:
        return jsonify({"error": "The requested command is not on the allowlist."}), 403

    # --- Input Sanitization ---
    safe_pattern = re.compile(r'^[a-zA-Z0-9\/._-]+$')
    for part in command_from_client:
        if not safe_pattern.match(part):
            return jsonify({"error": f"Invalid characters detected in command part: '{part}'"}), 400

    full_command = [TXG_EXECUTABLE] + command_from_client
    stdout_log, _, returncode = run_txg_command(full_command)
    content = stdout_log
    response = {"content": content}
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)