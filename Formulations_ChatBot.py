import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI
import streamlit as st
from streamlit_chat import message

# Initialize OpenAI client with the API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']  # Changed scope to allow writing

@st.cache_data(ttl=600)

def get_sheet_data(spreadsheet_id, range_name):
    try:
        # Load Google Sheets credentials from Streamlit secrets
        creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {str(e)}")
        return []

def generate_response(prompt, knowledge_base):
    try:
        full_prompt = f"Knowledge base:\n{knowledge_base}\n\nUser: {prompt}\nAI:"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500,
            n=1,
            temperature=0.2,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "I'm sorry, but I encountered an error while generating a response."

def save_response(spreadsheet_id, response):
    try:
        # Load Google Sheets credentials from Streamlit secrets
        creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES)

        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # Append the response to the 'Responses' tab
        response_range = 'Responses!A:A'
        value_range_body = {'values': [[response]]}
        sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range=response_range,
            valueInputOption='USER_ENTERED',
            body=value_range_body
        ).execute()

        st.success("Response saved successfully!")
    except Exception as e:
        st.error(f"Error saving response: {str(e)}")


def main():
    st.set_page_config(page_title="JYNN ", layout="wide")

    # Custom CSS for ChatGPT-like interface
    st.markdown("""
    <style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .stButton > button {
        width: 100%;
        border-radius: 20px;
    }
    .stMarkdown {
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("JYNN")

    # Get spreadsheet ID and range from Streamlit secrets
    spreadsheet_id = st.secrets["GOOGLE_SHEETS_ID"]
    range_name = st.secrets["GOOGLE_SHEETS_RANGE"]

    # Sidebar for refresh and clear buttons
    with st.sidebar:
        if st.button("Refresh Knowledge Base"):
            st.cache_data.clear()
            st.success("Knowledge base refreshed. Fetching latest data...")
            st.rerun()
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # Fetch knowledge base data
    knowledge_base = get_sheet_data(spreadsheet_id, range_name)
    
    if not knowledge_base:
        st.error("Failed to load knowledge base from Google Sheets.")
        return

    # Convert knowledge base to string
    knowledge_base_str = "\n".join([" ".join(row) for row in knowledge_base])

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            message(msg["content"], is_user=True, key=f"user_msg_{i}")
        else:
            message(msg["content"], key=f"ai_msg_{i}")

    # User input
    user_input = st.text_input("Ask your question:", key="user_input")

    # Send button
    if st.button("Send"):
        if user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Generate AI response
            response = generate_response(user_input, knowledge_base_str)

            # Add AI response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Clear the input box and rerun
            st.rerun()

    # Save button (only show if there's a response to save)
    if st.session_state.messages and st.session_state.messages[-1]['role'] == 'assistant':
        if st.button("Save Last Response"):
            last_response = st.session_state.messages[-1]['content']
            save_response(spreadsheet_id, last_response)

if __name__ == "__main__":
    main()