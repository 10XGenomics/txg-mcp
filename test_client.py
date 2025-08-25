# test_client.py
import json
import requests
import sys
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI()

# 1. Load the tool definitions
try:
    with open('tool.json', 'r') as f:
        tools = json.load(f)
except FileNotFoundError:
    print("Error: tool.json not found. Make sure it's in the same directory.")
    sys.exit(1)

# --- Display the available tools ---
tool_names = [tool['function']['name'] for tool in tools]
print(f"Available tools: {', '.join(tool_names)}")
# ------------------------------------

# 2. Get the prompt from the command-line argument
if len(sys.argv) > 1:
    user_prompt = sys.argv[1]
else:
    # If no argument is provided, print usage instructions and use a default prompt
    print("Usage: python test_client.py \"<Your question for the LLM>\"")
    user_prompt = "Can you list the projects available in my 10x account?"
    print(f"\nNo prompt provided. Using default: '{user_prompt}'")


messages = [{"role": "user", "content": user_prompt}]
print(f"\nSending prompt to OpenAI: \"{user_prompt}\"")

# --- Start the conversation loop ---
while True:
    # 3. Make an API call to OpenAI
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
            # Append the assistant's response to the message history
            messages.append(response_message)
            
            # 5. Execute the tool call and get the result
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"Tool: {function_name}, Arguments: {function_args}")

                mcp_server_url = "http://127.0.0.1:5001/"
                mcp_payload = {"tool_name": function_name, "parameters": function_args}
                
                print(f"Sending request to local MCP server...")
                mcp_response = requests.post(mcp_server_url, json=mcp_payload)
                mcp_response.raise_for_status()
                function_response = mcp_response.json()["content"]

                print("\n--- Response from MCP Server ---")
                print(function_response)
                print("--------------------------------")

                # 6. Append the tool's result to the message history
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            
            # Go back to the start of the loop to send the tool's output
            # back to the model for the next step.
            print("\nSending tool results back to OpenAI for final answer...")
            continue

        # 7. If there are no more tool calls, print the final answer and exit
        else:
            print("\n--- Final Answer from OpenAI ---")
            print(response_message.content)
            print("----------------------------------")
            break

    except requests.exceptions.RequestException as e:
        print(f"\nError calling MCP server: {e}")
        break
    except Exception as e:
        print(f"An error occurred during the OpenAI API call: {e}")
        break
