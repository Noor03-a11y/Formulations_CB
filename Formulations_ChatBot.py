import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI
import streamlit as st

# Initialize OpenAI client with the API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

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
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
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

def main():
    st.title("JYNN")

    # Get spreadsheet ID and range from Streamlit secrets
    spreadsheet_id = st.secrets["GOOGLE_SHEETS_ID"]
    range_name = st.secrets["GOOGLE_SHEETS_RANGE"]
    
    knowledge_base = get_sheet_data(spreadsheet_id, range_name)
    
    if knowledge_base:
        knowledge_base_str = "\n".join([" ".join(row) for row in knowledge_base])

        user_input = st.text_input("You:", "")
        if st.button("Send"):
            if user_input:
                response = generate_response(user_input, knowledge_base_str)
                st.text_area("AI:", value=response, height=200, max_chars=None, key=None)
    else:
        st.error("Failed to load knowledge base from Google Sheets.")

if __name__ == "__main__":
    main()
