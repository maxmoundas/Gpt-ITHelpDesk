# import os
# import requests
import json
import openai
import datetime

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
with open("state_machine.json") as file:
    state_machine = json.load(file)

# Get the OpenAI API key
with open('api_key.txt', 'r') as file:
    api_key = file.read().strip()

openai.api_key = api_key

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

            user_prompt = f"Act like a software engineer that is experiencing IT issues. Your problem given like a state machine looks like this in JSON format: {state_machine}. " \
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
    file.write(f"Number of steps taken: {interaction_count}")
    print(interaction_count)
