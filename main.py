import fastf1
import pandas as pd

def get_calendar(year: int):
    schedule = fastf1.get_event_schedule(2026)
    calendar = schedule[["EventName", "Session1", "Session1DateUtc", "Session2", "Session2DateUtc", "Session3", "Session3DateUtc", "Session4", "Session4DateUtc", "Session5", "Session5DateUtc"]]
    PreSeasonTesting_calendar = calendar[:2]
    race_calendar = calendar[2:]
    return race_calendar

def get_race_schedules(year):
    RaceSchedules = {}
    race_calendar = get_calendar(year)
    for index, race in race_calendar.iterrows():
        RaceSchedules[race["EventName"]] = {
                    "FP1": race["Session1DateUtc"],
                    "FP2": race["Session2DateUtc"],
                    "FP3": race["Session3DateUtc"],
                    "Qualifying": race["Session4DateUtc"],
                    "Race": race["Session5DateUtc"]
                }
    for key, value in RaceSchedules.items():
        print(f'{key}: {value["Race"]}')
        return RaceSchedules

def create_event(race, timestamp, isMainEvent):
    event={
        'summary': race,
        'start': {'datetime': timestamp},
        'end': {'datetime': timestamp + pd.Timedelta(hours=5)},
    }
    # code to add google calendar event
    
    if isMainEvent:
        'reminders'= {
            'userDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 1440},
                {'method': 'popup', 'minutes': 120}
            ]
        }

# print(WeekendSchedule.keys())
    

