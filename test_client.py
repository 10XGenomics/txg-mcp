# test_client.py
import sys
import os
import inspect # To dynamically find tools
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# Import the tools module itself, not the individual functions
import tools as tool_module

def get_llm(provider="openai"):
    """Initializes and returns the appropriate LLM based on the provider."""
    if provider == "anthropic":
        # Ensure your ANTHROPIC_API_KEY is set in your environment
        print("Using Anthropic (Claude)...")
        return ChatAnthropic(model="claude-3-sonnet-20240229")
    elif provider == "google":
        # Ensure your GOOGLE_API_KEY is set in your environment
        print("Using Google (Gemini)...")
        return ChatGoogleGenerativeAI(model="gemini-pro")
    else:
        # Default to OpenAI, ensures OPENAI_API_KEY is set
        print("Using OpenAI (GPT-4)...")
        return ChatOpenAI(model="gpt-4")

def main():
    """Main function to run the LangChain agent."""
    # --- 1. Setup: Dynamically discover tools ---
    available_tools = [
        obj for name, obj in inspect.getmembers(tool_module) 
        if isinstance(obj, BaseTool)
    ]
    
    if not available_tools:
        print("No tools found in tools.py. Make sure they are decorated with @tool.")
        sys.exit(1)

    tool_names = [tool.name for tool in available_tools]
    print(f"Available tools: {', '.join(tool_names)}")

    # --- 2. Get User Input ---
    if len(sys.argv) > 2:
        provider = sys.argv[1].lower()
        user_prompt = sys.argv[2]
    elif len(sys.argv) > 1:
        # If only one argument, it's the prompt, use default provider
        provider = "openai"
        user_prompt = sys.argv[1]
    else:
        print("Usage: python test_client.py [openai|anthropic|google] \"<Your question>\"")
        provider = "openai"
        user_prompt = "Can you list the projects available in my 10x account?"
        print(f"\nNo prompt provided. Using default: '{user_prompt}'")

    # --- 3. Create the Agent ---
    try:
        llm = get_llm(provider)
    except Exception as e:
        print(f"Error initializing LLM. Make sure your API key for '{provider}' is set.")
        print(e)
        sys.exit(1)

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that can interact with the 10x Genomics Cloud CLI."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Create the agent itself
    agent = create_tool_calling_agent(llm, available_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=available_tools, verbose=True)

    # --- 4. Run the Agent ---
    print(f"\nSending prompt: \"{user_prompt}\"")
    try:
        response = agent_executor.invoke({"input": user_prompt})
        print("\n--- Final Answer ---")
        print(response["output"])
        print("--------------------")
    except Exception as e:
        print(f"\nAn error occurred while running the agent: {e}")

if __name__ == "__main__":
    main()
