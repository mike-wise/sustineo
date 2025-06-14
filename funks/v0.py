import os
import json
import time
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from azure.identity import DefaultAzureCredential

import dotenv
dotenv.load_dotenv()

# 1. Define the function you want the agent to call
def fetch_weather(location: str) -> str:
    """
    Fetches the weather information for the specified location.
    :param location: The location to fetch weather for.
    :return: Weather information as a JSON string.
    """
    mock_weather_data = {"New York": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}
    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    return json.dumps({"weather": weather})

user_functions = {fetch_weather}

# 2. Register the function as a tool
functions = FunctionTool(functions=user_functions)

# 3. Create the agent and thread
project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
    api_version="latest",
)

agent = project_client.agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="my-agent",
    instructions="You are a helpful agent",
    tools=functions.definitions,
)

thread = project_client.agents.threads.create()

# 4. Send a message and process the run
message = project_client.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="What's the weather in New York?",
)

run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

while run.status in ["queued", "in_progress", "requires_action"]:
    time.sleep(1)
    run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
    if run.status == "requires_action":
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []
        for tool_call in tool_calls:
            if tool_call.name == "fetch_weather":
                # Parse arguments if needed; here we assume 'location' is passed
                args = json.loads(tool_call.arguments)
                output = fetch_weather(args.get("location", ""))
                tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
        project_client.agents.runs.submit_tool_outputs(
            thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
        )

# 5. Retrieve and display results
messages = project_client.agents.messages.list(thread_id=thread.id)
for message in messages:
    print(f"Role: {message['role']}, Content: {message['content']}")
