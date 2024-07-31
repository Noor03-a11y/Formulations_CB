import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI
import streamlit as st

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
    st.title("JYNN - Your AI Assistant")

    # Get spreadsheet ID and range from Streamlit secrets
    spreadsheet_id = st.secrets["GOOGLE_SHEETS_ID"]
    range_name = st.secrets["GOOGLE_SHEETS_RANGE"]

    # Add refresh button
    if st.button("Refresh Knowledge Base"):
        st.cache_data.clear()
        st.success("Knowledge base refreshed. Fetching latest data...")
        st.rerun()

    # Fetch knowledge base data
    knowledge_base = get_sheet_data(spreadsheet_id, range_name)
    
    if not knowledge_base:
        st.error("Failed to load knowledge base from Google Sheets.")
        return

    # Convert knowledge base to string
    knowledge_base_str = "\n".join([" ".join(row) for row in knowledge_base])

    # Create a container for chat history
    chat_container = st.container()

    # Initialize chat history in session state if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    with chat_container:
        for message in st.session_state.chat_history:
            st.text_area("You:" if message['role'] == 'user' else "AI:", value=message['content'], height=100, disabled=True)

    # User input
    user_input = st.text_input("Ask your question:", "")

    # Send button
    if st.button("Send Karo"):
        if user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Generate AI response
            response = generate_response(user_input, knowledge_base_str)

            # Add AI response to chat history
            st.session_state.chat_history.append({"role": "ai", "content": response})

            # Clear the input box and rerun
            st.rerun()

    # Save button (only show if there's a response to save)
    if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'ai':
        if st.button("Save Karo"):
            last_response = st.session_state.chat_history[-1]['content']
            save_response(spreadsheet_id, last_response)

    # Option to clear chat history
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

if __name__ == "__main__":
    main()

