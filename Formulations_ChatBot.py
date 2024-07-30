import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = r'C:\Users\Admin\Formulations_Interface\service_account.json'
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_sheet_data(spreadsheet_id, range_name):
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
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
    st.title("AI Chatbot with Google Sheets Knowledge Base")

    spreadsheet_id = '1Hfan1Go2uYTzytDwhApKVnWHoFCcVVHCGSlpTKXEUPY'
    range_name = 'Sheet1!A1:R'
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
