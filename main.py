#...we came in
import fastf1
import pandas as pd
import os
import shutil
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timezone
fastf1.set_log_level('ERROR')

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
    print(f"\nDone! Success: {success} Failed: {failed}")

def get_calendar(year: int):
    schedule = fastf1.get_event_schedule(year)
    if not schedule.empty:
        calendar = schedule[["EventName", "EventFormat", "Session1", "Session1DateUtc", "Session2", "Session2DateUtc", "Session3", "Session3DateUtc", "Session4", "Session4DateUtc", "Session5", "Session5DateUtc"]]
        race_calendar = calendar[calendar["EventFormat"].isin(["conventional", "sprint_qualifying"])].copy()
        racetimes = ["Session1DateUtc", "Session2DateUtc", "Session3DateUtc", "Session4DateUtc", "Session5DateUtc"]
        race_calendar[racetimes] = race_calendar[racetimes].apply(
            lambda col: col.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        )
        return race_calendar
    return None

def get_race_schedules(year):
    race_calendar = get_calendar(year)
    RaceSchedules = {}
    if race_calendar is  not None and not race_calendar.empty:
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
        'summary': "Buckle Up for F1 weekends this year. Use It's-Race-Week to schedule F1 races on your Google Calendar.",
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
    if  race_schedule:
        calendarEventList = []
        for EventName, races in race_schedule.items():
            grandPrix = create_event(EventName, races[f"{EventName} Practice 1"], isMainEvent=True)
            calendarEventList.append(grandPrix)
            for race, time in races.items():
                RaceEvent = create_event(race=race, raceTime=time, isMainEvent=False)
                calendarEventList.append(RaceEvent)
        add_events_to_calendar(calendarEventList, year)
        return "Success"
    return "Failed"

def printWelcomeMessage():
    os.system('cls' if os.name == 'nt' else 'clear')

    terminal_width, terminal_height = shutil.get_terminal_size()
    message_lines = [
        "========================================",
        "          🏁 Around The Corner 🏁         ",
        "    The F1 Google Calendar Auto-Sync    ",
        "========================================",
        "",
        "Never miss FP1, Quali, or any Race Day again.",
        "",
        "Login with your Google Account that is synced with your calendar and allow access to calendar"
    ]
    vertical_padding = (terminal_height - len(message_lines)) // 2

    for _ in range(max(0, vertical_padding)):
        print()
    for line in message_lines:
        print(line.center(terminal_width))
        
    print("\n")

printWelcomeMessage()
inputMessage = "Enter F1 season year: "
max_attempts = 5
terminal_width, terminal_height = shutil.get_terminal_size()
left_padding = ((terminal_width - len(inputMessage)) // 2)-3
for _ in range(max_attempts):
    try:
        centered_prompt = (" " * left_padding) + inputMessage
        inputYear = int(input(centered_prompt))
        print("\n"+"-"*terminal_width+"\n")
    except ValueError:
        print("Enter a valid year (number)")
        continue
    status = add_race_schedule_to_calendar(inputYear)
    if status == "Failed":
        print("---------------------------------------------------------------------------")
        print(f"Schedule not released for {inputYear} season yet try for a different year")
        print("---------------------------------------------------------------------------")
        print("\n")
    else:
        remind_rerunnig_next_year(inputYear)
        print("\n"+"-"*terminal_width+"\n")
        
        inputMessage = "You Are All Set for the Season!! Press Enter to close...\n\n"
        left_padding = ((terminal_width - len(inputMessage)) // 2)
        centered_prompt = (" " * left_padding) + inputMessage
        inputYear = input(centered_prompt)
        break
else:
    print("Too many failed attemps. Closing...")
#isn't this where...