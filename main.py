import fastf1
import pandas as pd

def get_calendar(year: int):
    schedule = fastf1.get_event_schedule(2026)
    calendar = schedule[["EventName", "Session1", "Session1DateUtc", "Session2", "Session2DateUtc", "Session3", "Session3DateUtc", "Session4", "Session4DateUtc", "Session5", "Session5DateUtc"]]
    PreSeasonTesting_calendar = calendar[:2]
    race_calendar = calendar[2:]
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
                    "FP1": race["Session1DateUtc"],
                    "FP2": race["Session2DateUtc"],
                    "FP3": race["Session3DateUtc"],
                    "Qualifying": race["Session4DateUtc"],
                    "Race": race["Session5DateUtc"]
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
    for key, value in event.items():
        print(f"{key}: {value}")
            
    # code to add google calendar event

def add_race_schedule_to_calendar(year: int):
    race_schedule = get_race_schedules(year)
    for EventName, races in race_schedule.items():
        create_event(EventName, races["FP1"], isMainEvent=True)
        for race, time in races.items():
            create_event(race=race, raceTime=time, isMainEvent=False)

# print(WeekendSchedule.keys())

add_race_schedule_to_calendar(2026)