# app.py
# A simple Flask server to expose the TXG CLI to LLMs via MCP.

import subprocess
import json
import re # Import the regular expressions module for sanitization
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- IMPORTANT ---
# Updated the path to a standard, trusted location for executables.
TXG_EXECUTABLE = "/usr/local/bin/txg"

def run_txg_command(command_parts):
    """
    Executes a TXG command securely using subprocess.Popen to capture
    real-time output from the command.
    Args:
        command_parts (list): A list of strings representing the command and its arguments.
                                e.g., ['/path/to/txg', 'projects', 'list']
    Returns:
        A tuple containing the full stdout/stderr log, and the final return code.
    """
    try:
        # Use Popen to start the process and get access to its output streams
        process = subprocess.Popen(
            command_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Redirect stderr to stdout
            text=True,
            bufsize=1 # Line-buffered
        )

        output_lines = []
        # Read the output line by line in real-time
        for line in iter(process.stdout.readline, ''):
            print(line, end='') # Print to server console for real-time monitoring
            output_lines.append(line)
        
        process.stdout.close()
        return_code = process.wait()
        
        full_output = "".join(output_lines)
        
        return full_output, None, return_code # Stderr is merged, so we return None for it

    except FileNotFoundError:
        return f"Error: '{TXG_EXECUTABLE}' not found. Is the path correct?", None, 1
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}", None, 1

# --- Updated Endpoint ---
# This new route matches the URL being called from your tools.py file.
@app.route('/run_command', methods=['POST'])
def handle_run_command():
    """
    Receives a command list, executes it, and returns the result.
    """
    data = request.get_json()
    command_from_client = data.get('command')

    if not command_from_client or not isinstance(command_from_client, list):
        return jsonify({"error": "Invalid or missing 'command' in request payload."}), 400

    # --- CHANGE 1: Input Sanitization ---
    # Sanitize each part of the incoming command to prevent command injection.
    # This regex allows alphanumeric characters, hyphens, underscores, dots, and slashes.
    # It explicitly disallows shell metacharacters like ;, |, &, $, etc.
    safe_pattern = re.compile(r'^[a-zA-Z0-9\/._-]+$')
    for part in command_from_client:
        if not safe_pattern.match(part):
            return jsonify({"error": f"Invalid characters detected in command part: '{part}'"}), 400

    # Prepend the executable path to the command from the client
    full_command = [TXG_EXECUTABLE] + command_from_client
    
    stdout_log, _, returncode = run_txg_command(full_command)

    # Even if the command fails, we return the log so the agent can see what happened.
    # The agent can decide if the error is critical or not.
    content = stdout_log

    response = {
        "content": content
    }
    return jsonify(response)

if __name__ == '__main__':
    # --- CHANGE 2: Bind to localhost ---
    # Listen only on the local loopback interface (127.0.0.1) for security.
    # This prevents the server from being exposed to the local network.
    app.run(host='127.0.0.1', port=5001)