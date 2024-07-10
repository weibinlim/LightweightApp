from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a student who just failed her exam."},
    {"role": "user", "content": "Compose a message to your professor asking for any tips to inmprove on the subject."}
  ]
)

print(completion.choices[0].message)