import fastf1
import pandas as pd
import json, os

def get_calendar(year: int):
    schedule = fastf1.get_event_schedule(2025)
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
    # for key, value in RaceSchedules.items():
    #     print(f'{key}: {value["Race"]}')
    
    return RaceSchedules

def create_event(race, raceTime, isMainEvent):
    minutes_list = [1440]if isMainEvent else [120, 90, 15]
    start= (raceTime - pd.Timedelta(hours=2)).isoformat() if isMainEvent else raceTime.isoformat()
    reminders = {
        'userDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': m} for m in minutes_list
        ]
    }
    event={
        'summary': race,
        'start': {
                'datetime': start,
                'timeZone': 'Asia/Kolkata'
            },
        'end': {
                'datetime': (raceTime + pd.Timedelta(hours=2)).isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
        'reminders': reminders
    }
    if os.path.exists("events.json"):
        with open("events.json","a") as f:
            json.dump(event, f)
            f.write("\n")
    return event
    # code to add google calendar event

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
# print(WeekendSchedule.keys())

add_race_schedule_to_calendar(2026)