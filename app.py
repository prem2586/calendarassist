


from langchain.tools import tool

@tool
def create_event(title: str, start_time: str, duration_minutes: int = 30) -> str:
    service = get_calendar_service()
    from datetime import datetime, timedelta
    import dateparser

    start_dt = dateparser.parse(start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event = {
        'summary': title,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Los_Angeles'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Los_Angeles'},
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return f"📅 Event created: {event.get('htmlLink')}"

@tool
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

with open("/mount/secure/credentials.json", "w") as f:
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



