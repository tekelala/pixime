import streamlit as st
import PyPDF2
from docx import Document
from io import BytesIO
import requests
import json
import pandas as pd
from PyPDF2 import PdfReader

# Define send message function
def create_text(prompt):
    api_url = "https://api.anthropic.com/v1/complete"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": st.secrets["API_KEY"]  # Use the API key from Streamlit's secrets
    }

    # Prepare the prompt for Claude
    conversation = f"Human: {prompt}\n\nAssistant:"

    # Define the body of the request
    body = {
        "prompt": conversation,
        "model": "claude-v1.3-100k",
        "temperature": 0,
        "max_tokens_to_sample": 10000,
        "stop_sequences": ["\n\nHuman:"]
    }

    # Make a POST request to the Claude API
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        st.error(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        st.error(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        st.error(f"Something went wrong: {err}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

    # Extract Claude's response from the JSON response
    result = response.json()

    # Return Claude's response as a string
    return result['completion']


def read_pdf(file):
    pdf_file = PdfReader(file)
    text = []
    for page in pdf_file.pages:
        text.append(page.extract_text())
    return " ".join(text)

def read_docx(file):
    document = Document(file)
    return " ".join([paragraph.text for paragraph in document.paragraphs])


st.title('Document Summary App')

# Initialize an empty DataFrame for storing document information
doc_info = pd.DataFrame(columns=['Name of the document', 'Summary in 150 words', 'Main arguments'])

uploaded_files = st.file_uploader("Upload a document", type=['pdf', 'doc', 'docx'], accept_multiple_files=True)

texts = {}

for uploaded_file in uploaded_files:
    file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
    #st.write(file_details)

    bytes_data = BytesIO(uploaded_file.getvalue())

    if uploaded_file.type == "application/pdf":
        text = read_pdf(bytes_data)
    elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        text = read_docx(bytes_data)
    else:
        st.error("Unsupported file type")

    texts[uploaded_file.name] = text

if st.button('Generar resumen'):
    for file_name, text in texts.items():
        with st.spinner(f'Generating summary for {file_name}...'):
            prompt1 = f'''Role: You are an AI assistant trained in legal expertise and your answers needs to be always in Spanish 
                        and just provide the text requested no need of titles or writting what you are doing.
                        Task: Create a summary of approximately 150 words for the following text {text}'''
 
                        
            prompt2 =  f'''Role: You are an AI assistant trained in legal expertise and your answers needs to be always in Spanish and just provide the text requested no need of titles or writting what you are doing

                        Task: Identify and extract each one of the legal and patentability arguments in the following text {text}. 
                        Double check to be sure you extracted all the arguments before writting your answer'''

            # The first section is the 100-word summary
            summary_100_words = create_text(prompt1)

            # The second section is the main legal arguments
            legal_arguments = create_text(prompt2)


            # Add the information to the DataFrame
            new_row = pd.DataFrame({'Name of the document': [file_name], 'Summary in 100 words': [summary_100_words], 'Main legal arguments': [legal_arguments]})
            doc_info = pd.concat([doc_info, new_row], ignore_index=True)

# Display the table
st.table(doc_info)