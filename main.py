import fastf1
import pandas as pd
import json, os
import sys
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timezone


SCOPES = ['https://www.googleapis.com/auth/calendar']

def delete_events_for_year(year):
    service = get_calendar_service()

    start_of_year = datetime(year, 1, 1, tzinfo=timezone.utc).isoformat()
    end_of_year = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).isoformat()

    print(f"⚠️ Deleting all events for year {year}...")

    page_token = None
    deleted = 0

    while True:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_year,
            timeMax=end_of_year,
            singleEvents=True,
            orderBy='startTime',
            pageToken=page_token
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            try:
                service.events().delete(
                    calendarId='primary',
                    eventId=event['id']
                ).execute()

                print(f"🗑 Deleted: {event.get('summary')}")
                deleted += 1

            except Exception as e:
                print(f"❌ Failed to delete: {event.get('summary')}")
                print("Error:", e)

        page_token = events_result.get('nextPageToken')
        if not page_token:
            break

    print(f"\n✅ Done! Deleted {deleted} events.")

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

def add_events_to_calendar(events, year):
    service = get_calendar_service()
    batch_size = 50
    success = 0
    failed = 0

    def get_existing_events(service, year):
        start_of_year = datetime(year, 1, 1, tzinfo=timezone.utc).isoformat()
        end_of_year = datetime(year+1, 1, 3, 23, 59, 59, tzinfo=timezone.utc).isoformat()
        
        result = service.events().list(
            calendarId='primary',
            timeMin=start_of_year,
            timeMax=end_of_year,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        existing = set()
        for e in result.get('items', []):
            props = e.get('extendedProperties', {}).get('private', {})
            if props.get('tag') != 'F1_EVENT':
                continue
            start = e['start'].get('dateTime')
            summary = e.get('summary')

            if start and summary:
                existing.add((summary, normalize_time(start)))
        return existing

    existing_events = get_existing_events(service, year)
    new_events = []
    for event in events:
        key = (event['summary'], normalize_time(event['start']['dateTime']))

        if key not in existing_events:
            new_events.append(event)
        else:
            print(f"Skipping duplicate: {event['summary']}")
    
    def callback(request_id, response, exception):
        nonlocal success, failed
        if exception:
            print(f"Error: {exception}")
            failed += 1
        else:
            print(f"Added: {response.get('summary')}")
            success += 1
    
    for i in range(0, len(new_events), batch_size):
        batch = service.new_batch_http_request()
        chunk = new_events[i:i + batch_size]

        for event in chunk:
            batch.add(
                service.events().insert(
                    calendarId='primary',
                    body=event
                ),
                callback=callback
            )

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
                    f"{race["EventName"]} {race["Session1"]}": race["Session1DateUtc"],
                    f"{race["EventName"]} {race["Session2"]}": race["Session2DateUtc"],
                    f"{race["EventName"]} {race["Session3"]}": race["Session3DateUtc"],
                    f"{race["EventName"]} {race["Session4"]}": race["Session4DateUtc"],
                    f"{race["EventName"]} {race["Session5"]}": race["Session5DateUtc"]
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
        'reminders': reminders,
        'extendedProperties': {
            'private': {
                'tag': 'F1_EVENT'
            }
        }
    }
    return event

def remind_rerunnig_next_year(year):
    event = [{
        'summary': "Buckle Up F1 weekends this year. Use It's-Race-Week to schedule F1 races on your Google Calendar.",
        'start': {
            'dateTime': f'{year+1}-01-03T13:00:00',
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': f'{year+1}-01-03T18:00:00',
            'timeZone': 'Asia/Kolkata',
        },
        'recurrence': [
            'RRULE:FREQ=YEARLY'
        ],'extendedProperties': {
            'private': {
                'tag': 'F1_EVENT'
            }
        }
    }]
    add_events_to_calendar(event, year+1)

def add_race_schedule_to_calendar(year: int):
    race_schedule = get_race_schedules(year)
    calendarEventList = []
    for EventName, races in race_schedule.items():
        grandPrix = create_event(EventName, races[f"{EventName} Practice 1"], isMainEvent=True)
        calendarEventList.append(grandPrix)
        for race, time in races.items():
            RaceEvent = create_event(race=race, raceTime=time, isMainEvent=False)
            calendarEventList.append(RaceEvent)
    print(len(calendarEventList))
    add_events_to_calendar(calendarEventList, year)

inputYear = int(input("enter the year for which u want your F1 calendar: "))
add_race_schedule_to_calendar(inputYear)
# delete_events_for_year(inputYear)
remind_rerunnig_next_year(inputYear)