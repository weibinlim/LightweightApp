from openai import OpenAI
from newsapi import NewsApiClient
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import date
from . import kw_processor
from . import web_scraper
from . import summarise

# Load environment variables from .env file
load_dotenv()

api_key  = os.getenv('NEWSAPI_KEY')
if not api_key:
    raise ValueError("No API key found. Please set the NEWSAPI_KEY environment variable.")
newsapi = NewsApiClient(api_key=api_key)

# Form a valid text to be input into the search engine, making use of all the data provided by the user
def input(list_of_keywords, additional_information, st_file):

    client = OpenAI()

    # Original Information
    prompt = "\n".join([
    f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n" 
    for pair in list_of_keywords
    ])
    
    if additional_information != '':
        add_info_processed = kw_processor.extract_company_info_text(additional_information)
        print(add_info_processed)
        # Additional Information (Others:)
        if (add_info_processed != []):
            prompt.join([f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n" for pair in add_info_processed])

    # Provide Direction
    prompt += "\nConcatenate the values of the key value pairs to a single string with each value being seperated by the following text in quotes ' AND '. Do this contcatenation for any other keywords extracted from the attached files, if any."
    vector_store = kw_processor.extract_company_info_file(st_file)
    
    if vector_store is not None:
        # Create assistant
        file_search_assistant = client.beta.assistants.create(
            name = "File Search Assistant",
            instructions = prompt,
            model = "gpt-3.5-turbo",
            tools = [{"type": "file_search"}],
        )

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
        
         # Create a thread and attach the file to the message
        thread = client.beta.threads.create(
          messages = [
            {
              "role": "user",
              "content": prompt,
              # Attach the new file to the message.
              "attachments": [
                { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
              ],
            }
          ]
        )

        print(thread.tool_resources.file_search)
        
        # Use the create and poll SDK helper to create a run and poll the status of
        # the run until it's in a terminal state.
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
        to_be_searched = message_content.value
        return to_be_searched

    else:
        search_param = client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages = [
                    {"role": "system", "content": "You are a linguist"},
                    {"role": "user", "content": prompt},
                  ],
            max_tokens = 50
        )
    
        # print(search_param.choices[0].message.content)
        to_be_searched = search_param.choices[0].message.content.replace('"', "")
        return to_be_searched

# Function to get the list of articles from NEWSAPI
# Returns:
#   A dictionary containing the following info: {source:, totalResults:, articles:}
#   within the aticles: portion
def get_article_list(query):
    api_result = newsapi.get_everything(q='Food',language='en', sort_by='publishedAt')
    article_list = api_result['articles']
    list_of_articles = []
    index = 0
    while index < 5:
        list_of_articles.append(article_list[index]['url'])
        index += 1
    print(list_of_articles)
    return list_of_articles

def prepare_prompt(data):
    prompt = "Here is some data from a JSON file:\n\n"
    try:
        prompt += web_scraper.read_json(data)
        prompt += "\nSummarise this data, making sure to capture the main points. "
        return prompt
    except FileNotFoundError:
        print('File not found:' + data)


def get_gpt_response(prompt):

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Summarise the following information" + prompt}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

# Main function
def tool(key_value_list, additional_info_str, list_of_files):

    to_be_searched = input(key_value_list, additional_info_str, list_of_files)
    list_of_latest_articles = get_article_list(to_be_searched)
    
    list_of_json_files = web_scraper.input_to_json_data(list_of_latest_articles)
    list_of_summarised_info = []

    for f in list_of_json_files:
        prompt = summarise.prepare_prompt(f)
        website_data_summary = summarise.response(prompt)
        list_of_summarised_info.append(website_data_summary)

    return list_of_summarised_info
