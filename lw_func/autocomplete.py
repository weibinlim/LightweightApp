# use autocomplete api
from openai import OpenAI
import requests
import ast
from . import kw_processor

# Form a valid text to be input into the search engine, making use of all the data provided by the user
# def input(list_of_keywords, additional_information, st_file):

training_data = [
    ["Incomplete phrase: macdonalds food",
    "Relevant Autocomplete phrase: [ mcdonald's food with most protein, mcdonald's food app, mcdonald's food calories, macdonalds food poisoning ] "],
    ["Incomplete phrase: coca cola food",
    "Relevant Autocomplete phrase: [ coca cola food truck, coca cola food label, coca cola food festival, coca cola food brands,  coca cola food truck citi field] "],
    ["Incomplete phrase: taco bell",
    "Relevant Autocomplete phrase: [ taco bell food poisoning 2024, taco bell food champion, taco bell food calculator, taco bell food calories, taco bell food weight in grams] "],
    ["Incomplete phrase: coca cola",
    "Relevant Autocomplete phrase: [ coca cola eshop, coca cola share price, coca cola k wave, coca cola stock,  ntuc coca cola promotion] "]
    ]

# Process input
# return:
#    key value list of key info
def process_input(list_of_keywords, additional_information, st_file):
    
    client = OpenAI()

    # Original Information
    list_of_info = list_of_keywords

    # Get Addtional Information
    if additional_information != '':
        add_info_processed = kw_processor.extract_company_info_text(additional_information)
        list_of_info.append(add_info_processed)
        
        # # Additional Information (Others:)
        # prompt.join([f"Key: {list(pair.keys())[0]}\nValue: {list(pair.values())[0] or 'N/A'}\n" 
        # for pair in add_info_processed
        # ])

    vector_store = kw_processor.extract_company_info_file(st_file)
    
    if vector_store is not None:
        # Create assistant
        file_search_assistant = client.beta.assistants.create(
            name = "File Search Assistant",
            instructions = "You are the best secretary in the world.",
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
              "content": "Extract the key information from the provided files and return them in a key value pairs in a python list format with no other additional text",
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
        
        # Text output by the model: Key Value Pairs of key info from the uploaded files
        to_be_searched = message_content.value
        print(to_be_searched)
        list_of_info.append(ast.literal_eval(to_be_searched))

    return get_query(list_of_info)


# Craft keyword queries for autocompletion
# return:
#    python list of possible keywords
def get_query(k_list):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an excellent marketing agent"},
            {"role": "user", "content": "Look through the provided list and return a list of possible combinations of keywords that should be incomplete phrases. These phrases should include the Company Name and will be inputed into a autocomplete api to retrieve long tail keywords. The returned message should be in the form of a python list with no other extra inputs. Provided List:" + str(k_list)}
        ],
        max_tokens=300
    )
    return ast.literal_eval(response.choices[0].message.content)


# Autocomplete suggestions from DuckDuckGo
#    returns: List of autocomplete long tail keywords
def get_duckduckgo_suggestions(query):
    url = f"https://duckduckgo.com/ac/?q={query}"
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    suggestions = response.json()
    return [suggestion['phrase'] for suggestion in suggestions]


# Autocomplete suggestions from Google
#    returns: List of autocomplete long tail keywords
def get_google_suggestions(query):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={query}"
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    suggestions = response.json()
    return suggestions[1]


# Autocomplete suggestions from Yahoo
#    returns: List of autocomplete long tail keywords
def get_yahoo_suggestions(query):
    url = f"https://search.yahoo.com/sugg/gossip/gossip-us-ura/?output=json&command={query}"
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    suggestions = response.json()
    return [item['key'] for item in suggestions['gossip']['results']]


# Chat completion to extract relevant keywords
#   returns: string representation of a list of 5 relevant long tail keywords
def filter_kw(autocompleted_list):
    suggestions = ''.join(map(lambda x: x + ',',map(str,autocompleted_list)))
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an excellent marketing agent"},
            {"role": "user", "content":"Look through the provided list and pick out 5 long tail keywords that you think can help management understand what people are searching for with regards to your company. Give me an output in the form of a list [keyword1, keyword2]. Here are some examples:" 
             + str(training_data) + ". Your output should follow the format [phrase1, phrase2, phrase3, phrase4, phrase5], however these are just examples and should not be used as the actual output." + "Here is the actual list of long tail keywords:" + suggestions}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

# Main function to call other functions
#   returns: list of 5 relevant long tail keywords
def main(list_of_keywords, additional_information, st_file):
    overall_suggestions = []
    list_of_uncomplete = process_input(list_of_keywords, additional_information, st_file)
    print(list_of_uncomplete)
    for uncomplete in list_of_uncomplete:
        ddg_completed = get_duckduckgo_suggestions(uncomplete)
        for keyword in ddg_completed:
            overall_suggestions.append(keyword)
        google_completed = get_google_suggestions(uncomplete)
        for keyword in google_completed:
            overall_suggestions.append(keyword)
        yahoo_completed = get_yahoo_suggestions(uncomplete)
        for keyword in yahoo_completed:
            overall_suggestions.append(keyword)
    print('\nOverall Suggestions:', overall_suggestions)
    print('\nEnd\n')
    return ast.literal_eval(filter_kw(overall_suggestions))