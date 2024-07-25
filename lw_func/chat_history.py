import json

# Function to add to chat history
def add_to_history(id, message, chat_history_list):
    if id == 0:
        chat_history_list.append(message)
        print('History for user added successfully')
    elif id == 1:
        chat_history_list.append({"role": "assistant", "content": message})
        print('History for assistant added successfully')
    else:
        print('Invalid id')

# Function to save chat history to a JSON file
def save_chat_history(chat_history, filename = 'chat_history.json'):
    with open(filename, 'w') as file:
        json.dump(chat_history, file, indent = 4)

# Function to load chat history from a JSON file
def load_chat_history(filename = 'chat_history.json'):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to load the string representation of the chat history
def extract_chat_history(filename = 'chat_history.json'):
    try:
        with open(filename, 'r') as file:
            json_data = json.load(file)
            json_string = json.dumps(json_data, indent=4)
            print(json_string)
            return json_string
    except FileNotFoundError:
        return []

# Function to erase chat history from a JSON file
def reset_chat_history(filename = 'chat_history.json'):
     with open(filename, 'w') as file:
        json.dump([], file)