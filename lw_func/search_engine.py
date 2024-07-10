from openai import OpenAI
from duckduckgo_search import DDGS
from fp.fp import FreeProxy
import time
from datetime import date
from . import kw_processor
from . import web_scraper
from . import summarise

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
            results = DDGS().text(search_string, max_results = 5)
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


# # Make http requests with the link and scrape the data, then dump the data into an external json file
# # Args:
# #    url_link: a string of the url of the website
# def web_scraper(url_link, destination_file):
#     options = webdriver.FirefoxOptions()
#     options.headless = True
#     driver_path = 'web_driver/geckodriver'
#     # print(options)
#     driver = webdriver.Firefox(options=options)

#     try:
#         # Navigate to the website
#         driver.get(url_link)

#         WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
#         body_elements = driver.find_elements(By.TAG_NAME, 'body')
#         # print(body_elements)
#         elements = []
#         for element in body_elements:
#             elements.append(element.text) 
        
#         with open(destination_file, 'w') as file:
#             json.dump(elements, file, indent = 4)
        
#     finally:
#         driver.quit()


# # Takes in the keywords
# # Args:
# #    list of key value pairs
# # Returns:
# #    number of json files used to store data (5)
# def get_json_data(list_of_keywords, add_info, list_of_files):
    
#     to_be_searched = kw_processor.input(list_of_keywords, add_info, list_of_files, 'search engine')
    
#     list_of_hottest_links = ddg_search(to_be_searched)

#     file_index = 1
#     for result in list_of_hottest_links:
#         d_file = str(file_index) + 'web_data_scraped.json'
#         print(d_file)
#         web_scraper(result['href'], d_file)
#         file_index += 1
#         print(file_index)

#     return file_index - 1
    

# def input_to_json_data(key_value_list, add_info, files):
    
#     number_of_json_files = get_json_data(key_value_list, add_info, files)
#     list_of_json_files = []
#     index = 1
#     while number_of_json_files != 0:
#         list_of_json_files.append(str(index) + 'web_data_scraped.json')
#         number_of_json_files -= 1
#         index += 1

#     # List of TextIOWrapper????
#     print(list_of_json_files)
#     return list_of_json_files


# def read_json(file_name):

#     try:
#         print(file_name)
#         with open(file_name, 'r') as file:
#             json_data = json.load(file)
#             json_string = json.dumps(json_data, indent=4)
#             return json_string
#     except FileNotFoundError:
#         return ''
    
def prepare_prompt(data):
    prompt = "Here is some data from a JSON file:\n\n"
    today = date.today()
    try:
        prompt += web_scraper.read_json(data)
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

    to_be_searched = input(key_value_list, additional_info_str, list_of_files)
    list_of_hottest_links = ddg_search(to_be_searched)
    
    list_of_json_files = web_scraper.input_to_json_data(list_of_hottest_links)
    list_of_summarised_info = []

    for f in list_of_json_files:
        prompt = summarise.prepare_prompt(f)
        website_data_summary = summarise.response(prompt)
        list_of_summarised_info.append(website_data_summary)

    return list_of_summarised_info

