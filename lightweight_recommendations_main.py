import streamlit as st
from pathlib import Path
from openai import OpenAI
import csv
import lw_func.search_engine
import json

st.title('Lightweight Recommendations App')

st.write('Company Information (Fill where applicable)')

st_company_name = st.text_input('Company Name')
st_industry = st.text_input('Industry')
st_company_size = st.text_input('Company Size')
st_location = st.text_input('Location (Country)')
st_target_audience = st.text_input('Target Audience')
st_others = st.text_input('Others:')

# st_role = st.text_input("What's My Role?", 'Marketer, Professor, Student etc.')
# st_info = st.text_input('What would you like me to do today?', "What would you like me to do today?")


# List of files
st_file = st.file_uploader(label = "Upload File (Recommended)", type = None, accept_multiple_files = True, key = None, help = None, on_change = None, args = None, kwargs = None, disabled = False, label_visibility = "visible")

# Temporary list to store chat history
# chat_history = lw_func.chat_history.load_chat_history()

list_of_info = [
    {"Company Name" : st_company_name},
    {"Industry" : st_industry},
    {"Company Size" : st_company_size},
    {"Location" : st_location},
    {"Target Audience" : st_target_audience},
    {"Additional Information" : st_others}
]


# # Function to get output from model
# def get_chat_response(role, info, files, history):
#     client = OpenAI()

#     user_input = [{"role": "system", "content": st_role}, {"role": "user", "content": st_info}]
#     if len(st_file) > 0:
#         # Create assistant
#         file_search_assistant = client.beta.assistants.create(
#             name = "File Search Assistant",
#             instructions = st_role + "." + st_info,
#             model = "gpt-3.5-turbo",
#             tools = [{"type": "file_search"}],
#         )

#         # Create a vector store
#         vector_store = client.beta.vector_stores.create(name = "Context Files")

#         # Use the upload and poll SDK helper to upload the files, add them to the vector store,
#         # and poll the status of the file batch for completion.
#         file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
#           vector_store_id = vector_store.id, files = st_file
#         )
#         print(file_batch.status)
#         print(file_batch.file_counts)
        
#         # Update assistant to use new Vector Store
#         file_search_assistant = client.beta.assistants.update(
#             assistant_id = file_search_assistant.id,
#             tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}},
#         )

#         # Upload the user provided file to OpenAI
#         for f in st_file:
#             message_file = client.files.create(
#               file = f, purpose = "assistants"
#             )
        
#         # List contatining the input format, including the file attachment
#         user_input = [{"role": "assistant", "content": st_role}, 
#                       {"role": "user", "content": st_info, 
#                        "attachments": [
#                            { "file_id": message_file.id, "tools": [{"type": "file_search"}]}
#                             ]}]
#         lw_func.chat_history.add_to_history(0, user_input, history)
        
#          # Create a thread and attach the file to the message
#         thread = client.beta.threads.create(
#           messages = [
#             {
#               "role": "user",
#               "content": st_info + ". This is the chat history" + extract_chat_history(),
#               # Attach the new file to the message.
#               "attachments": [
#                 { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
#               ],
#             }
#           ]
#         )

#         print(thread.tool_resources.file_search)
        
#         # Use the create and poll SDK helper to create a run and poll the status of
#         # the run until it's in a terminal state.*
#         run = client.beta.threads.runs.create_and_poll(
#             thread_id = thread.id, assistant_id = file_search_assistant.id
#         )
        
#         messages = list(client.beta.threads.messages.list(thread_id = thread.id, run_id = run.id))
        
#         message_content = messages[0].content[0].text
#         annotations = message_content.annotations
#         citations = []
#         for index, annotation in enumerate(annotations):
#             message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
#             if file_citation := getattr(annotation, "file_citation", None):
#                 cited_file = client.files.retrieve(file_citation.file_id)
#                 citations.append(f"[{index}] {cited_file.filename}")
        
#         # Text output by the model
#         output = message_content.value
#         lw_func.chat_history.add_to_history(1, output, history)
#         return output

#     else:
#         # if there is no file uploaded for context
#         # List contatining the input format
#         user_input = [{"role": "system", "content": st_role}, {"role": "user", "content": st_info}]
#         lw_func.chat_history.add_to_history(0, user_input, history)
#         gpt_answer = client.chat.completions.create(
#             model = "gpt-3.5-turbo",
#             messages = [
#                 {"role": "system", "content": st_role},
#                 {"role": "user", "content": extract_chat_history()}
#               ]
#             )

#         # Text output by the model
#         output = gpt_answer.choices[0].message.content
#         lw_func.chat_history.add_to_history(1, output, history)
#         return output


def gen_recommendation(list_of_summarised_info):

    client = OpenAI()

    print(list_of_info)
    print(list_of_summarised_info)
    prompt = "Given the following information, provide me with the top 2 developments of the day relevant to my company. Here is the following information:\n"
    # prompt = prompt.join([
    # f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n" 
    # for pair in list_of_info]).join(list_of_summarised_info)

    for pair in list_of_info:
        prompt += f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n"

    for info in list_of_summarised_info:
        prompt += info
        
    print(prompt)
    gpt_answer = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": "You are a very experienced secretary."},
            {"role": "user", "content": prompt},
          ]
        )

    result = gpt_answer.choices[0].message.content
    return result


if st.button('Generate Text Output', key = 'button1'):

    answer = gen_recommendation(lw_func.search_engine.tool(list_of_info, st_others, st_file))
    st.write("From Us:", answer)

if st.button('Reset', key = 'button2'):

    with open('1web_data_scraped.json', 'w') as file:
        json.dump([], file)
    with open('2web_data_scraped.json', 'w') as file:
        json.dump([], file)
    with open('3web_data_scraped.json', 'w') as file:
        json.dump([], file)
    with open('4web_data_scraped.json', 'w') as file:
        json.dump([], file)
    with open('5web_data_scraped.json', 'w') as file:
        json.dump([], file)