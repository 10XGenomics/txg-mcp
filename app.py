# app.py
# A simple Flask server to expose the TXG CLI to LLMs via MCP.

import subprocess
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

def run_txg_command(command_parts):
    """
    Executes a TXG command securely using subprocess.
    Args:
        command_parts (list): A list of strings representing the command and its arguments.
                                e.g., ['txg', 'runs', 'list']
    Returns:
        A tuple containing stdout, stderr, and the return code.
    """
    try:
        # Execute the command.  captures stdout/stderr.
        #  decodes them as text.  prevents raising an
        # exception on non-zero exit codes, so we can handle errors gracefully.
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        # This error occurs if the 'txg' command is not found in the system's PATH.
        return None, "Error: 'txg' command not found. Is the TXG CLI installed and in your PATH?", 1
    except Exception as e:
        return None, f"An unexpected error occurred: {str(e)}", 1

@app.route('/', methods=['POST'])
def handle_mcp_request():
    """
    Main endpoint for handling MCP requests.
    """
    data = request.get_json()
    tool_name = data.get('tool_name')
    parameters = data.get('parameters', {})

    command = []
    
    # --- Route the tool_name to the appropriate TXG command ---
    if tool_name == 'list_projects':
        command = ['txg', 'projects', 'list', '--output-format=json']

    elif tool_name == 'list_runs':
        command = ['txg', 'runs', 'list', '--output-format=json']
        # Add optional project-id filter if provided
        project_id = parameters.get('project_id')
        if project_id:
            command.extend(['--project-id', project_id])

    elif tool_name == 'get_run':
        run_id = parameters.get('run_id')
        if not run_id:
            return jsonify({
                "error": "Missing required parameter: run_id"
            }), 400
        command = ['txg', 'runs', 'get', run_id, '--output-format=json']

    else:
        return jsonify({
            "error": f"Unknown tool_name: {tool_name}"
        }), 404

    # --- Execute the command and format the response ---
    stdout, stderr, returncode = run_txg_command(command)

    if returncode != 0:
        # If the command failed, return the error from stderr
        content = f"Error executing command.\nExit Code: {returncode}\nError: {stderr}"
    else:
        # On success, return the output from stdout
        content = stdout

    # The MCP response format is a simple JSON object with a "content" key.
    response = {
        "content": content
    }
    return jsonify(response)

if __name__ == '__main__':
    # Run the Flask app on port 5001
    app.run(host='0.0.0.0', port=5001)
