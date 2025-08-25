# app.py
# A simple Flask server to expose the TXG CLI to LLMs via MCP.

import subprocess
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- IMPORTANT ---
# Updated the path to a standard, trusted location for executables.
TXG_EXECUTABLE = "/usr/local/bin/txg"

def run_txg_command(command_parts):
    """
    Executes a TXG command securely using subprocess.
    Args:
        command_parts (list): A list of strings representing the command and its arguments.
                                e.g., ['/path/to/txg', 'projects', 'list']
    Returns:
        A tuple containing stdout, stderr, and the return code.
    """
    try:
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return None, f"Error: '{TXG_EXECUTABLE}' not found. Is the path correct?", 1
    except Exception as e:
        return None, f"An unexpected error occurred: {str(e)}", 1

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

    # Prepend the executable path to the command from the client
    full_command = [TXG_EXECUTABLE] + command_from_client
    
    stdout, stderr, returncode = run_txg_command(full_command)

    if returncode != 0:
        content = f"Error executing command.\nExit Code: {returncode}\nError: {stderr}"
    else:
        content = stdout

    response = {
        "content": content
    }
    return jsonify(response)

if __name__ == '__main__':
    # Run the Flask app on port 5001
    app.run(host='0.0.0.0', port=5001)
