from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from fp.fp import FreeProxy
import time
from datetime import date
import json

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
        
        with open(destination_file, 'w') as file:
            json.dump(elements, file, indent = 4)
        
    finally:
        driver.quit()


# Takes in the keywords
# Args:
#    list of key value pairs
# Returns:
#    number of json files used to store data (5)
def get_json_data(list_of_hottest_links):

    file_index = 1
    for result in list_of_hottest_links:
        d_file = str(file_index) + 'web_data_scraped.json'
        print(d_file)
        web_scraper(result, d_file)
        file_index += 1
        print(file_index)

    return file_index - 1
    

def input_to_json_data(list_of_hottest_links):
    
    number_of_json_files = get_json_data(list_of_hottest_links)
    list_of_json_files = []
    index = 1
    while number_of_json_files != 0:
        list_of_json_files.append(str(index) + 'web_data_scraped.json')
        number_of_json_files -= 1
        index += 1

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