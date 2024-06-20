from openai import OpenAI
from pathlib import Path
import requests
from duckduckgo_search import DDGS
# For webscraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import csv


# Function to extract key company info from others prompt
# return A list of key value pair
def extract_company_info(company_info_string):
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


# Get search results from DuckDuckGo search engine
# return a list of top 5 search results [{Title:, URL:, Snippet:}]
def ddg_search(search_string):
    results = DDGS().text(search_string, max_results = 5)
    print(results)
    return results

# Make http requests with the link and scrape the data
# Args:
#    url_link: a string of the url of the website
# Returns:
#    idk yet
def web_scraper(url_link, destination_file):
    options = webdriver.FirefoxOptions()
    options.headless = True
    driver_path = /Users/weibinlim/Downloads/web_driver/geckodriver
    driver = webdriver.Firefox(executable_path = driver_path, options = options)

    try:
        # Navigate to the website
        driver.get(url_link)
    
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".content")))
    
        # Locate job listings (adjust the selector to match the website's structure)
        elements = driver.find_elements(By.CSS_SELECTOR, ".content")

        # Write the data onto a seperate csv file
        with open('web_data_scraped.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            for data in elements:
                writer.writerow(data)

    finally:
        driver.quit()


# Get content
# Returns:
#    number of csv files used to store data
def get_csv_data(list_of_keywords):

    client = OpenAI()
    prompt = "\n".join([f"Key: {pair['key']}\nValue: {pair['value']}\n" for pair in data])
    prompt += "\nCraft a text based on the given keywords to be inputted into a search engine to get the latest updates around the world related to these keywords"

    search_param = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = [
                {"role": "system", "content": "You are a linguist"},
                {"role": "user", "content": prompt}
              ]
        max_tokens = 50
    )

    to_be_searched = search_param.choices[0].message.content

    list_of_hottest_links = ddg_search(to_be_searched)

    file_index = 1
    for link in list_of_hottest_links:
        d_file = file_index + 'web_data_scraped.csv'
        web_scraper(link, d_file)
        
        file_index += 1

    return file_index
    

def input_to_csv_data(key_value_list):
    
    number_of_csv_files = get_csv_data(key_value_list)
    list_of_csv_files = []
    index = 1
    while number_of_csv_files != 0:
        list_of_csv_data.append(index + 'web_data_scraped.csv')
        number_of_csv_files -= 1

    return list_of_csv_files


def read_csv(file_name):
    data = []
    with open(file_name, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)
    return data

    
def prepare_prompt(data):
    prompt = "Here is some data from a CSV file:\n\n"
    for row in data:
        prompt += ", ".join(f"{key}: {value}" for key, value in row.items()) + "\n"
    prompt += "\nWhat insights can you provide based on this data?"
    return prompt


def get_gpt_response(prompt):

    client - OpenAI()
    response = client.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300  # Adjust as needed
    )
    return response['choices'][0]['message']['content'].strip()


# Main function
def tool(key_value_list):

    list_of_csv_files = input_to_csv_data(key_value_list)
    list_of_summarised_info = []

    for f in list_of_csv_files:
        website_data = read_csv(f)
        prompt = prepare_prompt(website_data)
        website_data_summary = get_gpt_response(prompt)
        lit_of_summarised_info.append(website_data_summary)
        
    return list_of_summarised_info

