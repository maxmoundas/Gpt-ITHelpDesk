# import os
# import requests
import json
import openai
import datetime
import networkx as nx

# Get current date and time
now = datetime.datetime.now()
timestamp = now.strftime('%Y%m%d_%H%M')

# To get the name of the file for the conversation
filename = f'conversation_{timestamp}.txt'


# def call_gpt(prompt, role):
#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[
#             {"role": role, "content": f"{prompt}"}
#         ]
#     )
#     return response.choices[0].message['content'].strip()

def call_gpt(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message['content'].strip()


# Load the state machine from a file
with open("state_machine_more_complex.json") as file:
    state_machine = json.load(file)

# Get the OpenAI API key
with open('api_key.txt', 'r') as file:
    api_key = file.read().strip()

openai.api_key = api_key

# Function to calculate the cyclomatic complexity
def calculate_cyclomatic_complexity(graph):
    e = sum(len(targets) for targets in graph.values())  # number of edges
    n = len(graph)  # number of nodes
    p = 1  # assuming one connected component
    cc = e - n + 2 * p
    return cc

# Function to calculate the average degree
def calculate_average_degree(graph):
    total_edges = sum(len(targets) for targets in graph.values())
    total_nodes = len(graph)
    return total_edges / total_nodes if total_nodes > 0 else 0


# Creating a NetworkX graph from the state machine graph
G = nx.DiGraph()

# Adding nodes and edges to the NetworkX graph
for state in state_machine['states']:
    state_name = state['name']
    actions = state.get('actions', [])

    # Adding the current state as a node
    G.add_node(state_name)

    # Adding edges based on actions
    for action in actions:
        next_state = action['nextState']
        G.add_edge(state_name, next_state)

# Initialize the state
state = "Initial"
user_response = ""

# Limit the number of interactions
max_interactions = 20
interaction_count = 0

# Initialize the conversation history
conversation_history = []

with open(filename, 'w') as file:
    # Main loop

    # problem could be that user_response != "Y" when it should be
    phrase = "The user's response is: "
    while interaction_count < max_interactions:
        # Fetch actions for the current state
        actions = next(s['actions'] for s in state_machine['states'] if s['name'] == state)

        # Generate actions using GPT-3
        if len(user_response) != 0:
            print("user_response:", user_response)

            user_response = user_response.replace(phrase, "")
            action_prompt = f"The user's response is: {user_response}. The current state is {state}. The suggested actions are {actions}."
            conversation_history.append({"role": "assistant", "content": action_prompt})
            action_response = call_gpt(conversation_history)
            file.write(f"*******************************************************\n")
            file.write(f"Assistant's response: {action_response}\n")
            print("action_response: ", action_response, "\n")
            # might wanna change the prompt what is the user's response?
            # this prompt doesn't work either
            # It's like ChatGPT forgot about the first user and action prompts
            user_prompt = f"The actions taken are {action_response}."
            conversation_history.append({"role": "user", "content": user_prompt})
            user_response = call_gpt(conversation_history)
            file.write(f"*******************************************************\n")
            user_response = user_response.replace(phrase, "")
            file.write(f"User's response: {user_response}\n")
            print("User's response: ", user_response, "\n")
        else:
            action_prompt = f"You are IT Help Desk. You are given state machine in a JSON format for problem of a user. " \
                            f"This is the state machine: {state_machine}. Current state is 'initial', you need to help them reach 'Desired' state. " \
                            f"Tell them what to do step-by-step and expect progress from the user. Describe your action plan in a chain-of-thought. Tell what next steps to take. Treat it like a conversation."
            conversation_history.append({"role": "assistant", "content": action_prompt})
            action_response = call_gpt(conversation_history)
            file.write(f"Assistant's response: {action_response}\n")
            print("first action_response: ", action_response, "\n")

            user_prompt = f"Act like an old grandma that is experiencing IT issues. Your problem given like a state machine looks like this in JSON format: {state_machine}. " \
                          f"The initial state is 'initial' and I will help you get to 'desired'. Follow my orders step by step and report to me with the result."
            conversation_history.append({"role": "user", "content": user_prompt})
            user_response = call_gpt(conversation_history)
            file.write(f"*******************************************************\n"
                       f"User's response: {user_response}\n")
            print("first user_response: ", user_response, "\n")

        # Update the state based on the user's responses and the defined transitions
        # this might be a problem too, is user_response correct here?
        for action in actions:
            print("searching for action: ", user_response)
            if action['name'] in user_response:
                state = action['nextState']
                break
        print(f"The real current state is {state}\n")
        interaction_count += 1

        if state == "Desired":
            break
    file.write(f"Number of steps taken: {interaction_count}\n")
    node_count = len(state_machine["states"])
    edge_count = sum(len(state["actions"]) for state in state_machine["states"])
    graph_density = edge_count / (node_count * (node_count - 1)) if node_count > 1 else 0
    file.write(f"Node Count: {node_count}\n")
    file.write(f"Edge Count: {edge_count}\n")
    file.write(f"Graph Density: {graph_density}\n")

    # Calculating Cyclomatic Complexity and Average Degree
    cyclomatic_complexity = calculate_cyclomatic_complexity(state_machine)
    average_degree = calculate_average_degree(state_machine)
    file.write(f"Cyclomatic Complexity: {cyclomatic_complexity}\n")
    file.write(f"Average Degree: {average_degree}\n")

    # Calculating Average Path Length (APL)
    # APL is calculated only if the graph is strongly connected, otherwise it's infinite or undefined
    if nx.is_strongly_connected(G):
        average_path_length = nx.average_shortest_path_length(G)
    else:
        # Handling the case where the graph is not strongly connected
        # Computing average path length for each connected component
        apl_values = []
        for component in nx.strongly_connected_components(G):
            subgraph = G.subgraph(component)
            apl_values.append(nx.average_shortest_path_length(subgraph))

        # Averaging over all strongly connected components
        average_path_length = sum(apl_values) / len(apl_values) if apl_values else float('inf')

    # Calculating Network Diameter (ND)
    # ND is the maximum shortest path length in the graph
    network_diameter = nx.diameter(G) if nx.is_strongly_connected(G) else max(nx.diameter(G.subgraph(c)) for c in nx.strongly_connected_components(G))
    file.write(f"Average Path Length: {average_path_length}\n")
    file.write(f"Network Diameter: {network_diameter}\n")

    print(interaction_count)
