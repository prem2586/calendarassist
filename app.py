from langchain.tools import tool

from langchain.tools import tool
import json

@tool
def create_event(data: str) -> str:
    """Create a calendar event. Input should be a JSON string with 'title' and 'time'."""
    try:
        parsed = json.loads(data)
        title = parsed["title"]
        time = parsed["time"]
        # call Google Calendar API here
        return f"Created event '{title}' at {time}"
    except Exception as e:
        return f"Error parsing input: {e}"

@tool(description="List calendar events for a given date.")
def list_events(date: str) -> str:
    service = get_calendar_service()
    import dateparser
    from datetime import timedelta

    start = dateparser.parse(date)
    end = start + timedelta(days=1)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start.isoformat() + 'Z',
        timeMax=end.isoformat() + 'Z',
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    if not events:
        return "No events found."
    
    return "\n".join(f"{e['summary']} at {e['start'].get('dateTime', e['start'].get('date'))}" for e in events)


from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(temperature=0, openai_api_key="your-key")
agent = initialize_agent([create_event, list_events], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

with open("credentials.json", "w") as f:
    f.write(st.secrets["GOOGLE_CREDENTIALS_JSON"])

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service


import streamlit as st

st.title("📅 Agentic Google Calendar Assistant")
query = st.text_input("What would you like me to do?")

if st.button("Run"):
    response = agent.run(query)
    st.success(response)



