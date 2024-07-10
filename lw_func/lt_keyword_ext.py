# main folder for the long tail keyword exractor

from duckduckgo_search import DDGS
from fp.fp import FreeProxy
import time
from openai import OpenAI
from . import kw_processor
from . import web_scraper

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

        # Additional Information (Others:)
        prompt.join([f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n" 
        for pair in add_info_processed
        ])

    # Provide Direction    
    prompt += "\nCraft a text based on the given information to be inputted into a search engine to get the latest updates around the world related to this information"

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

# Get search results from DuckDuckGo search engine
# return a list of top 5 search results [{Title:, URL:, Snippet:}]
def ddg_search(search_string):
    e_count = 0
    results = None
    while True:
        try:
            proxy = FreeProxy(google=True).get()
            print(f"Using proxy: {proxy}")
            print(f"Search string: {search_string}")
            time.sleep(5)
            # To be edited
            results = DDGS().text(search_string, max_results = 1)
            time.sleep(5)
            break
        except Exception as e:
            print(e)
            print("Retry")
            e_count += 1
    if results is not None:
        url_list = []
        for result in results:
            print(result)
            url_list.append(result['href'])
        print(url_list)
        return url_list
    else:
        return ['Nothing']

def search_kw(json_string):

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a very sharp assistant with great foresight"},
            {"role": "user", "content": "Extract any important information in phrases no longer than 10 words from the following information and output them in a python list format: [phrase 1, phrase 2, phrase 3] without any additional text." + json_string}
        ],
        max_tokens=300
    )
    print(response.choices[0].message.content) 
    return response.choices[0].message.content

def main(list_of_keywords, additional_information, st_file):

    search_string = input(list_of_keywords, additional_information, st_file)
    json_files = web_scraper.input_to_json_data(ddg_search(search_string))
    keywords = []
    for file in json_files:
        keywords.append(search_kw(web_scraper.read_json(file)))
    print(keywords)
    return keywords

