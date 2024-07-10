from openai import OpenAI


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
        
        result = company_info.choices[0].message.content
        kv_pairs = result.split(',')
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