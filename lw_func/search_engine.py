from openai import OpenAI
from pathlib import Path
import requests
from duckduckgo_search import DDGS
# For webscraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from fp.fp import FreeProxy
from bs4 import BeautifulSoup
import time
from datetime import date
import csv
import json


# Extracts key company info from the 'Others:' portion
# Returns: 
    # A list of key value pairs
def extract_company_info_text(company_info_string):
    
    if company_info_string is not None: 
        client = OpenAI()
        company_info = client.chat.completions.create(
                model = "gpt-3.5-turbo",
                messages = [
                    {"role": "system", "content": "You are the best assistant in the world, especially in terms of picking out keywords from text"},
                    {"role": "user", "content": "What are the key company information in the following text. Represent the info in key value pairs. For example, 'key1:value1, key2:value2', with the key being the property and the value being the relevant info for that property."}
                  ]
                )
        kv_pairs = kv_string.split(',')
        kv_list = [pair.split(':') for pair in kv_pairs]
        return kv_list
    else:
        return []


# Create a vector store for any uploaded files
def extract_company_info_file(files):

    if (len(files) > 0):
        client = OpenAI()
        # Create a vector store
        vector_store = client.beta.vector_stores.create(name = "Context Files")
    
        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
          vector_store_id = vector_store.id, files = files
        )
        print(file_batch.status)
        print(file_batch.file_counts)
    
        return vector_store
    else:
        return None
    

# Form a valid text to be input into the search engine, making use of all the data provided by the user
def search_engine_input(list_of_keywords, additional_information, st_file):

    client = OpenAI()

    # Original Information
    prompt = "\n".join([
    f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n" 
    for pair in list_of_keywords
])

    # Additional Information (Others:)
    prompt.join([f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n" 
    for pair in additional_information
])

    # Provide Direction
    prompt += "\nCraft a text based on the given information to be inputted into a search engine to get the latest updates around the world related to this information"

    vector_store = extract_company_info_file(st_file)
    
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
    while True:
        if (e_count < 5):
            try:
                proxy = FreeProxy().get()
                print(f"Using proxy: {proxy}")
                print(f"Search string: {search_string}")
                time.sleep(5)
                results = DDGS().text(search_string, max_results = 5)
                # print(results)
                return results
            except Exception as e:
                print(e)
                print("Retry")
                e_count += 1
        else:
            return ['nothing']
            


# Make http requests with the link and scrape the data, then dump the data into an external json file
# Args:
#    url_link: a string of the url of the website
def web_scraper(url_link, destination_file):
    options = webdriver.FirefoxOptions()
    options.headless = True
    driver_path = 'web_driver/geckodriver'
    # print(options)
    driver = webdriver.Firefox(options=options)

    try:
        # Navigate to the website
        driver.get(url_link)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        body_elements = driver.find_elements(By.TAG_NAME, 'body')
        # print(body_elements)
        elements = []
        for element in body_elements:
            elements.append(element.text) 
        # print(elements)
        
        # Write the data onto a seperate csv file
        # with open(destination_file, mode='w') as file:
        #     writer = csv.writer(file)
        #     for data in elements:
        #         writer.writerow(data)

        
        with open(destination_file, 'w') as file:
            json.dump(elements, file, indent = 4)
        
    finally:
        driver.quit()


# Takes in the keywords
# Args:
#    list of key value pairs
# Returns:
#    number of json files used to store data (5)
def get_json_data(list_of_keywords, add_info, list_of_files):
    
    to_be_searched = search_engine_input(list_of_keywords, add_info, list_of_files)
    
    list_of_hottest_links = ddg_search(to_be_searched)

    file_index = 1
    for result in list_of_hottest_links:
        d_file = str(file_index) + 'web_data_scraped.json'
        print(d_file)
        web_scraper(result['href'], d_file)
        file_index += 1
        print(file_index)

    return file_index - 1
    

def input_to_json_data(key_value_list, add_info, files):
    
    number_of_json_files = get_json_data(key_value_list, add_info, files)
    list_of_json_files = []
    index = 1
    while number_of_json_files != 0:
        list_of_json_files.append(str(index) + 'web_data_scraped.json')
        number_of_json_files -= 1
        index += 1

    # List of TextIOWrapper????
    print(list_of_json_files)
    return list_of_json_files


def read_json(file_name):

    try:
        print(file_name)
        with open(file_name, 'r') as file:
            json_data = json.load(file)
            json_string = json.dumps(json_data, indent=4)
            return json_string
    except FileNotFoundError:
        return ''
        
    # data = []
    # with open(file_name, mode='r') as file:
    #     csv_reader = csv.DictReader(file)
    #     for row in csv_reader:
    #         data.append(row)
    # return data

    
def prepare_prompt(data):
    prompt = "Here is some data from a JSON file:\n\n"
    today = date.today()
    # for row in data:
    #     prompt += ", ".join(f"{key}: {value}" for key, value in row.items()) + "\n"
    # prompt += "\nWhat insights can you provide based on this data?"
    # return prompt
    try:
        prompt += read_json(data)
        prompt += "\nSummarise this data, making sure to capture the main points regarding the most recent updates. "
        prompt += "The date today is" + str(today)
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

    list_of_json_files = input_to_json_data(key_value_list, additional_info_str, list_of_files)
    list_of_summarised_info = []

    for f in list_of_json_files:
        prompt = prepare_prompt(f)
        website_data_summary = get_gpt_response(prompt)
        list_of_summarised_info.append(website_data_summary)

    return list_of_summarised_info

