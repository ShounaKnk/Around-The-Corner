import fastf1
import pandas as pd

schedule = fastf1.get_event_schedule(2026)

"""
    "EventName", "Session1", "Session1DateUtc", "Session2", "Session2DateUtc", "Session3", "Session3DateUtc", "Session4", "Session4DateUtc", "Session5", "Session5DateUtc"
""" 
calendar = schedule[["EventName", "Session1", "Session1DateUtc", "Session2", "Session2DateUtc", "Session3", "Session3DateUtc", "Session4", "Session4DateUtc", "Session5", "Session5DateUtc"]]
PreSeasonTesting_calendar = calendar[:2]
race_calendar = calendar[2:]

# print(schedule.columns)

# print(PreSeasonTesting_calendar)
# print(race_calendar)

WeekendSchedule = {}

for index, race in race_calendar.iterrows():
    WeekendSchedule[race["EventName"]] = {
                "FP1": race["Session1DateUtc"],
                "FP2": race["Session2DateUtc"],
                "FP3": race["Session3DateUtc"],
                "Qualifying": race["Session4DateUtc"],
                "Race": race["Session5DateUtc"]
            }

print(WeekendSchedule.keys())