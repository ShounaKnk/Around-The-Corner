import fastf1
import pandas as pd
import json, os
import sys
from datetime import datetime
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime


SCOPES = ['https://www.googleapis.com/auth/calendar']

def normalize_time(dt_str):
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(microsecond=0)

def get_resource_path(filename):
    import sys
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

def get_calendar_service():
    creds = None
    TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".calendar_token.json")
    CREDENTIALS_PATH = get_resource_path("credentials.json")

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

def add_events_to_calendar(events):
    service = get_calendar_service()
    batch_size = 50
    success = 0
    failed = 0

    def get_existing_events():
        result = service.events().list(
            calendarId='primary',
            maxResults=250,
            singleEvents=True
        ).execute()

        existing = set()
        for e in result.get('items', []):
            start = e['start'].get('dateTime')
            summary = e.get('summary')
            if start and summary:
                existing.add((summary, normalize_time(start)))
        return existing

    existing_events = get_existing_events()

    def callback(request_id, response, exception):
        nonlocal success, failed, existing_events

        if exception:
            print(f"Error: {exception}")
            failed += 1
        else:
            summary = response.get('summary')
            start = response['start'].get('dateTime')

            print(f"✅ Added: {summary}")
            success += 1

            existing_events.add((summary, normalize_time(start)))

    for i in range(0, len(events), batch_size):
        batch = service.new_batch_http_request()
        chunk = events[i:i + batch_size]

        for event in chunk:
            key = (event['summary'], normalize_time(event['start']['dateTime']))

            if key not in existing_events:
                batch.add(
                    service.events().insert(
                        calendarId='primary',
                        body=event
                    ),
                    callback=callback
                )
            else:
                print(f"Skipping duplicate: {event['summary']}")

        if batch._requests:
            batch.execute()
            print(f"Batch {i//batch_size + 1} completed")

    print("\nDone!")
    print(f"Success: {success}")
    print(f"Failed: {failed}")

def get_calendar(year: int):
    schedule = fastf1.get_event_schedule(year)
    calendar = schedule[["EventName", "EventFormat", "Session1", "Session1DateUtc", "Session2", "Session2DateUtc", "Session3", "Session3DateUtc", "Session4", "Session4DateUtc", "Session5", "Session5DateUtc"]]
    race_calendar = calendar[calendar["EventFormat"].isin(["conventional", "sprint_qualifying"])]
    racetimes = ["Session1DateUtc", "Session2DateUtc", "Session3DateUtc", "Session4DateUtc", "Session5DateUtc"]
    race_calendar[racetimes] = race_calendar[racetimes].apply(
        lambda col: col.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    )
    return race_calendar

def get_race_schedules(year):
    RaceSchedules = {}
    race_calendar = get_calendar(year)
    for index, race in race_calendar.iterrows():
        RaceSchedules[race["EventName"]] = {
                    race["Session1"]: race["Session1DateUtc"],
                    race["Session2"]: race["Session2DateUtc"],
                    race["Session3"]: race["Session3DateUtc"],
                    race["Session4"]: race["Session4DateUtc"],
                    race["Session5"]: race["Session5DateUtc"]
                }
    
    return RaceSchedules

def create_event(race, raceTime, isMainEvent):
    minutes_list = [1440]if isMainEvent else [120, 90, 15]
    start= (raceTime - pd.Timedelta(hours=2)).isoformat() if isMainEvent else raceTime.isoformat()
    reminders = {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': m} for m in minutes_list
        ]
    }
    event={
        'summary': race,
        'start': {
                'dateTime': start,
                'timeZone': 'Asia/Kolkata'
            },
        'end': {
                'dateTime': (raceTime + pd.Timedelta(hours=2)).isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
        'reminders': reminders
    }
    return event

def add_race_schedule_to_calendar(year: int):
    race_schedule = get_race_schedules(year)
    calendarEventList = []
    for EventName, races in race_schedule.items():
        grandPrix = create_event(EventName, races["Practice 1"], isMainEvent=True)
        calendarEventList.append(grandPrix)
        for race, time in races.items():
            RaceEvent = create_event(race=race, raceTime=time, isMainEvent=False)
            calendarEventList.append(RaceEvent)
    print(len(calendarEventList))
    add_events_to_calendar(calendarEventList)

inputYear = int(input("enter the year for which u want your F1 calendar: "))
add_race_schedule_to_calendar(inputYear)