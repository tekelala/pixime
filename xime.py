import streamlit as st
import PyPDF2
from docx import Document
from io import BytesIO
import requests
import json
import pandas as pd
from PyPDF2 import PdfReader

# Define send message function
def create_summary(prompt):
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
        "model": "claude-v1.3",
        "max_tokens_to_sample": 500,
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
doc_info = pd.DataFrame(columns=['Name of the document', 'Summary in 100 words', 'Main legal arguments'])

uploaded_files = st.file_uploader("Upload a document", type=['pdf', 'doc', 'docx'], accept_multiple_files=True)

for uploaded_file in uploaded_files:
    file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
    st.write(file_details)

    bytes_data = BytesIO(uploaded_file.getvalue())

    if uploaded_file.type == "application/pdf":
        text = read_pdf(bytes_data)
    elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        text = read_docx(bytes_data)
    else:
        st.error("Unsupported file type")

if st.button('Generar resumen'):
    for uploaded_file in uploaded_files:
        with st.spinner(f'Generating summary for {uploaded_file.name}...'):
            prompt = f'''Role: You are an AI assistant trained in legal expertise. 

                        Task 1: 
                        Please provide a summary of approximately 100 words for the following document: 
                        {uploaded_file.name}
                        {text}

                        Task 2: 
                        Identify and explain the main legal arguments in the document.'''

            summary = create_summary(prompt)
            # Split the summary into two sections: the 100-word summary and the main legal arguments
            summary_sections = summary.split("\n\n")

            # The first section is the 100-word summary
            summary_100_words = summary_sections[0]

            # The second section is the main legal arguments
            legal_arguments = summary_sections[1]

            # Add the information to the DataFrame
            doc_info = doc_info.append({'Name of the document': uploaded_file.name, 'Summary in 100 words': summary_100_words, 'Main legal arguments': legal_arguments}, ignore_index=True)

# Display the table
st.table(doc_info)