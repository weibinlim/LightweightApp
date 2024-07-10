import streamlit as st
import json
from pathlib import Path
from openai import OpenAI

st.title('Lightweight App')

st_role = st.text_input("What's My Role?", 'Marketer, Professor, Student etc.') 

st_info = st.text_input('What would you like me to do today?', "What would you like me to do today?")

# List of files
st_file = st.file_uploader(label = "Upload File (Recommended)", type = None, accept_multiple_files = True, key = None, help = None, on_change = None, args = None, kwargs = None, disabled = False, label_visibility = "visible")

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

# Temporary list to store chat history
chat_history = load_chat_history()

# Function to get output from model
def get_chat_response(role, info, files, history):
    client = OpenAI()

    user_input = [{"role": "system", "content": st_role}, {"role": "user", "content": st_info}]
    if len(st_file) > 0:
        # Create assistant
        file_search_assistant = client.beta.assistants.create(
            name = "File Search Assistant",
            instructions = st_role + "." + st_info,
            model = "gpt-3.5-turbo",
            tools = [{"type": "file_search"}],
        )

        # Create a vector store
        vector_store = client.beta.vector_stores.create(name = "Context Files")

        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
          vector_store_id = vector_store.id, files = st_file
        )
        print(file_batch.status)
        print(file_batch.file_counts)
        
        # Update assistant to use new Vector Store
        file_search_assistant = client.beta.assistants.update(
            assistant_id = file_search_assistant.id,
            tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}},
        )

        # Upload the user provided file to OpenAI
        for f in st_file:
            message_file = client.files.create(
              file = f, purpose = "assistants"
            )
        
        # List contatining the input format, including the file attachment
        user_input = [{"role": "assistant", "content": st_role}, 
                      {"role": "user", "content": st_info, 
                       "attachments": [
                           { "file_id": message_file.id, "tools": [{"type": "file_search"}]}
                            ]}]
        add_to_history(0, user_input, history)
        
         # Create a thread and attach the file to the message
        thread = client.beta.threads.create(
          messages = [
            {
              "role": "user",
              "content": st_info + ". This is the chat history" + extract_chat_history(),
              # Attach the new file to the message.
              "attachments": [
                { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
              ],
            }
          ]
        )

        print(thread.tool_resources.file_search)
        
        # Use the create and poll SDK helper to create a run and poll the status of
        # the run until it's in a terminal state.*
        run = client.beta.threads.runs.create_and_poll(
            thread_id = thread.id, assistant_id = file_search_assistant.id
        )
        
        messages = list(client.beta.threads.messages.list(thread_id = thread.id, run_id = run.id))
        
        message_content = messages[0].content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")
        
        # Text output by the model
        output = message_content.value
        add_to_history(1, output, history)
        return output

    else:
        # if there is no file uploaded for context
        # List contatining the input format
        user_input = [{"role": "system", "content": st_role}, {"role": "user", "content": st_info}]
        add_to_history(0, user_input, history)
        gpt_answer = client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages = [
                {"role": "system", "content": st_role},
                {"role": "user", "content": extract_chat_history()}
              ]
            )

        # Text output by the model
        output = gpt_answer.choices[0].message.content
        add_to_history(1, output, history)
        return output


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
        

if st.button('Generate Text Output', key = 'button1'):

    client = OpenAI()
    response = get_chat_response(st_role, st_info, st_file, chat_history)
    save_chat_history(chat_history)
    st.write('Your Answer:', response)
    # print(extract_chat_history())

if st.button('Reset Chat History', key = 'button2'):
    reset_chat_history()
