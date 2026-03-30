# Around The Corner - F1 Google Calendar Auto-Sync

A Python script that automatically fetches the Formula 1 race schedule for a given season and synchronizes it directly to your Google Calendar. Never miss FP1, Quali, or a Race Day again!

## Features

- **Automatic F1 Scheduling**: Fetches the official F1 schedule for any given year using the `fastf1` library.
- **Local Time Conversion**: Converts all session times (Practice 1/2/3, Qualifying, Sprint, Race) to your local timezone (`Asia/Kolkata`).
- **Smart Reminders**: 
  - Main events (Grand Prix): Sets a 24-hour reminder before the event block begins.
  - Other sessions: Sets reminders 2 hours, 90 minutes, and 15 minutes prior to the session.
- **Duplicate Prevention**: Intelligently checks your calendar for existing entries tagged as `F1_EVENT` to prevent duplicate events from being created if the script is run multiple times.
- **Batch Processing**: Uses the Google Calendar API batch request feature to efficiently insert events without hitting typical rate limits.
- **Annual Rerun Reminder**: Automatically schedules a recurring yearly reminder at the start of the next year to run the script and sync the new season's schedule.

## How it Works (`main.py`)

The logic of this project is entirely self-contained within `main.py`.

1. **Authentication**: Upon running, the script initiates a local OAuth2 flow. It opens a browser window for you to log into your Google Account and authorize calendar access.
2. **Data Retrieval**: It prompts you for an F1 season year and uses `fastf1.get_event_schedule(year)` to pull the schedule of all conventional and sprint format weekends.
3. **Calendar Integration**: It parses the active sessions into Google Calendar event dictionary formats, attaching custom reminders and a private extended property tag (`F1_EVENT`) for easy future identification.
4. **Synchronization**: It fetches events currently existing on your Google Calendar for that year, filters out duplicates, and batch inserts the rest.

## Prerequisites & Installation

- Python 3.x
- Necessary Python packages can be installed via pip:
  ```bash
  pip install fastf1 pandas google-auth-oauthlib google-api-python-client
  ```

## Usage

Simply run the main script from your terminal:

```bash
python main.py
```

1. Enter the year of the F1 season when prompted (e.g., `2024`).
2. Follow the browser prompt to securely log in with your Google Account and grant Calendar access.
3. Once authorized, sit back while the events populate directly into your primary calendar!
