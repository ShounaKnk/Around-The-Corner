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

## Installation & Usage

### 🪟 For Windows Users (Executable)

If you are on Windows, you don't need to install Python. You can simply run the compiled executable file directly!

1. Download the `.exe` file from the **Releases** section of this GitHub repository.
2. Double-click the downloaded executable to run the program.
3. When prompted in the terminal window, enter the year of the F1 season (e.g., `2025`).
4. A web browser will open. Securely log in with your Google Account and grant Google Calendar access.
5. Once authorized, return to the terminal and watch as the F1 events populate directly into your primary calendar!

### 🍎 For Mac/Linux Users (Run Locally)

macOS and Linux users will need to run the Python script locally from the source code.

**Prerequisites:** You must have [Python 3.x](https://www.python.org/downloads/) installed on your system.

1. **Clone the repository** to your local machine:
   ```bash
   git clone https://github.com/ShounaKnk/Around-The-Corner.git
   cd Around-The-Corner
   ```

2. **Install the required dependencies** via `pip`:
   ```bash
   pip install fastf1 pandas google-auth-oauthlib google-api-python-client
   ```

3. **Run the script**:
   ```bash
   python main.py
   ```

4. When prompted in the terminal window, enter the year of the F1 season (e.g., `2025`).
5. A web browser will open. Securely log in with your Google Account and grant Google Calendar access.
6. Once authorized, return to the terminal and watch as the F1 events populate directly into your primary calendar!

## Screenshots & Walkthrough

Here is a step-by-step look at what it's like to use the app:

### 1. Launching the App
When you start the script, you will be greeted by the welcome screen. Here, you'll be prompted to enter the year of the F1 season you'd like to sync (e.g., `2026`).
![Welcome Screen](/Screenshots/1_welcome.png)

### 2. Authorization
After entering the year, the app generates a unique Google OAuth link. It will usually open in your browser automatically, or you can manually copy and paste the provided URL to authorize the app.
![OAuth URL Generation](/Screenshots/2_oauth_link.png)

### 3. Google Consent Warning
Because this is a custom, unverified local application connecting to your own calendar, Google will display a "Google hasn't verified this app" safeguard warning. This is perfectly normal for personal scripts! To proceed:
- Click **Advanced** at the bottom.
- Click on **Go to f1-calendar (unsafe)** to continue and grant calendar permissions.
![Google Consent Warning](/Screenshots/3_google_consent.png)

### 4. Real-time Synchronization
Once you successfully grant access, return to the terminal. You'll see the script aggressively fetching and adding every session—Practice 1/2/3, Sprint, Qualifying, and the Main Race—for every Grand Prix directly to your primary calendar.
![Sync Processing](/Screenshots/4_sync_progress.png)

### 5. Completion
Once all events are batched and added, the terminal drops a wrap-up message with the total number of events synced. The script also automatically plants a reminder in your calendar for January of the *following* year, so you'll never forget to run it for the next season!
![Completion Screen](/Screenshots/5_success.png)
