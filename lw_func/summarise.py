from openai import OpenAI
from datetime import date
from . import web_scraper

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


def response(prompt):

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