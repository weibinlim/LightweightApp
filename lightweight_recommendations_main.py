import streamlit as st
from pathlib import Path
from openai import OpenAI
from lw_func import search_engine
from lw_func import news_api
from lw_func import lt_keyword_ext
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

    if st_others is None:
        st_others = 'Empty'
    if st_file is None:
        st_file = 'Empty'
    print(st_others)
    print(st_file)
    answer = gen_recommendation(search_engine.tool(list_of_info, st_others, st_file))
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

if st.button('Test News API', key = 'button3'):
    
    print(news_api.tool(list_of_info, st_others, st_file))

if st.button('Test Keyword Extractor', key = 'button4'):
    
    print(lt_keyword_ext.main(list_of_info, st_others, st_file))