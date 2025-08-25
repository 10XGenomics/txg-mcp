# test_client.py
import json
import requests
from openai import OpenAI

# Initialize the OpenAI client
# It will automatically pick up the OPENAI_API_KEY from your environment
client = OpenAI()

# 1. Load the tool definitions from your tool.json file
# The new format is a simple list, so we don't need to access a "tools" key.
with open('tool.json', 'r') as f:
    tools = json.load(f)

# 2. Define the user's prompt
messages = [
    {"role": "user", "content": "Can you list the projects available in my 10x account?"}
    # Try other prompts too!
    # "What are the runs for project 'project-123'?"
    # "Get me the details for run 'run-abc-456'"
]

print("Sending prompt to OpenAI...")

# 3. Make the first API call to OpenAI
try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 4. Check if the model wants to call a tool
    if tool_calls:
        print("OpenAI model decided to call a tool.")
        
        # For this example, we'll just handle the first tool call
        tool_call = tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        print(f"Tool: {function_name}")
        print(f"Arguments: {function_args}")

        # 5. Call your local MCP server
        mcp_server_url = "http://127.0.0.1:5001/"
        mcp_payload = {
            "tool_name": function_name,
            "parameters": function_args
        }
        
        print(f"\nSending request to local MCP server at {mcp_server_url}...")
        
        try:
            mcp_response = requests.post(mcp_server_url, json=mcp_payload)
            mcp_response.raise_for_status() # Raise an exception for bad status codes
            
            # 6. Print the result from your server
            print("\n--- Response from MCP Server ---")
            # Use .json() to parse the JSON response and then re-format it for pretty printing
            print(json.dumps(mcp_response.json(), indent=2))
            print("--------------------------------")

        except requests.exceptions.RequestException as e:
            print(f"\nError calling MCP server: {e}")

    else:
        print("OpenAI model responded without a tool call.")
        print(response_message.content)

except Exception as e:
    print(f"An error occurred during the OpenAI API call: {e}")
