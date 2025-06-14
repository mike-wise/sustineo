import os
import json
import time
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from azure.identity import DefaultAzureCredential

import dotenv
dotenv.load_dotenv()

def dump_principal_id():
    aad_credentials = DefaultAzureCredential()
    token = aad_credentials.get_token("https://management.azure.com/.default")
    import base64
    import json
    payload = token.token.split('.')[1]
    payload += '=' * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload)
    claims = json.loads(decoded)
    print(claims)
    
# dump_principal_id()

# 1. Define the functions you want the agent to call
def fetch_weather(location: str) -> str:
    """
    Fetches the weather information for the specified location.
    :param location: The location to fetch weather for.
    :return: Weather information as a JSON string.
    """
    mock_weather_data = {"New York": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}
    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    return json.dumps({"weather": weather})
    

def fetch_population(location: str) -> str:
    """
    Fetches the population information for the specified location.
    :param location: The location to fetch population for.
    :return: population information as a JSON string.
    """
    mock_population_data = {"New York": "8470000", "London": "8900000", "Tokyo": "14040000"}
    population = mock_population_data.get(location, "Population data not available for this location.")
    return json.dumps({"population": population})    

user_functions = {fetch_weather, fetch_population}

# 2. Register the function as a tool
functions = FunctionTool(functions=user_functions)

# 3. Create the agent and thread
project_client = AIProjectClient(
    subscription_id=os.environ["SUBSCRIPTION_ID"],
    resource_group_name=os.environ["RESOURCE_GROUP_NAME"],
    project_name=os.environ["PROJECT_NAME"],    
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

agent = project_client.agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="my-agent",
    instructions="You are a helpful agent",
    tools=functions.definitions,
)
agid = agent["id"]
print(f"----- agent id: {agid}")

thread = project_client.agents.create_thread()
thid = thread["id"]
print(f"----- thread id: {thid}:")


print("------------------Starting Thread -------------------------")

def do_run(project_client, agid, thid ):
    print(f"============= starting run ==============")
    run = project_client.agents.create_run(thread_id=thid, agent_id=agid)
    while run.status in ["queued", "in_progress", "requires_action"]:
        print("run status:",run.status)
        time.sleep(1)
        run = project_client.agents.get_run(thread_id=thid, run_id=run.id)
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for tool_call in tool_calls:
                fname = tool_call.function["name"]
                dbmsg = f"{type(tool_call)}-{fname}"
                print(dbmsg)
                # print(dir(tool_call))
                # print(tool_call.items)
                if fname in ["fetch_weather","fetch_population"]:
                    # Parse arguments if needed; here we assume 'location' is passed
                    args = json.loads(tool_call.function["arguments"])
                    if fname == "fetch_weather":
                        output = fetch_weather(args.get("location", ""))
                    elif fname == "fetch_population":
                        output = fetch_population(args.get("location", ""))
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
            project_client.agents.submit_tool_outputs_to_run(
                thread_id=thid, run_id=run.id, tool_outputs=tool_outputs
            )
    print(f"============= finished run ==============")
            
def print_messages(project_client, thid):
    messages = project_client.agents.list_messages(thread_id=thid)
    msgs = []
    for elem in messages["data"]:
        role = elem["role"]
        vdict = elem["content"][0]
        vtyp = vdict["type"]
        if vtyp == "text":
            txmsg = vdict["text"]["value"]
            m = f"{role}:{vtyp}:{txmsg}"
        else:
            m = f"{role}:{vtyp}"
        msgs.append(m)
        
    nmsg = len(msgs)
    print(f"============= Messages ============== {nmsg}")
    for m in msgs:
        print(m)
        
    
# 4. Send a message and process the run
message = project_client.agents.create_message(
    thread_id=thid,
    role="user",
    content="What's the weather in New York? What's the population in London?"
)


do_run(project_client, agid, thid)

print_messages(project_client, thid)

message = project_client.agents.create_message(
    thread_id=thid,
    role="user",
    content="What's the weather in Tokyo? What's the population in New York?"
)

do_run(project_client, agid, thid)

print_messages(project_client, thid)
