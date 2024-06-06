import streamlit as st
import json

st.title('Lightweight App')

st_role = st.text_input('Enter the Role', 'Marketer, Professor, Student etc.') 

st_info = st.text_input('Enter The Context', 'What would you like me to do today?')

st_file = st.file_uploader(label = "Upload File (Optional)", type = None, accept_multiple_files = True, key = None, help = None, on_change = None, args = None, kwargs = None, disabled = False, label_visibility = "visible")

if st.button('Generate Text Output'):

    from openai import OpenAI
    client = OpenAI()

    text_output = ""
    
    if st_file is not None:
        text = ""
        for i in range(len(st_file)): 
        	for line in st_file[i]:
        		text += str(line)

        text = "Summarise the following text" + text
        
        text_summarised = client.chat.completions.create(
          model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": "You are an academic."},
            {"role": "user", "content": text}
          ]
        )

        text_output = text_output + " " + text_summarised.choices[0].message.content
    
    prompt = client.chat.completions.create(
      model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": st_role},
            {"role": "user", "content": st_info}
          ]
        )
        
    prompt_output = prompt.choices[0].message.content

    if (text_output != ""):

        combined = client.chat.completions.create(
          model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": st_role},
            {"role": "user", "content": "Give me an ouput based on the two texts" + prompt_output + text_output}
          ]
        )

        combined_output = combined.choices[0].message.content

        st.write('Your answer:')
        
        st.write(combined_output)
    else:
        st.write('Your answer:')
        
        st.write(prompt_output)
    