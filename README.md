# StudyOS — Study Operating System

A functional JEE preparation web app built with Python, Flask, SQLite, HTML, CSS and JavaScript.

## Features

- Personalized dashboard and exam countdown
- Daily motivation
- Mock-test entry and permanent history
- Total, average and percentage calculations
- Subject performance analysis
- Smart study recommendations
- Physics, Chemistry and Mathematics chapter tracker
- Completion, revision and PYQ tracking
- Daily task manager
- Pomodoro-style focus timer
- Permanent study-session tracking
- Progress analytics
- Notes / formula / revision journal
- Mistake log
- Settings
- Local SQLite database

## Run it

1. Install Python 3.10+.
2. Open a terminal inside this folder.
3. Run:

```bash
pip install -r requirements.txt
python app.py
```

4. Open the local address Flask prints, normally:

`http://127.0.0.1:5000`

Your data is stored in `studyos.db`.

## Important

The current "smart" assistant is intentionally local/rule-based. It uses saved scores, chapter completion, revisions, study time and mistakes. No API key is required.

A real AI API can be added later for explanations, personalized question generation and conversational study assistance.


## Installable app version

StudyOS is now a Progressive Web App (PWA). Once the Flask server is hosted on an HTTPS domain, supported browsers can install it like an app. The app has:
- its own StudyOS icon
- standalone app window
- mobile-friendly metadata
- service-worker caching
- an in-app Install StudyOS button when the browser supports installation

For a public installable version, deploy this same project to an HTTPS host. The SQLite database remains local to the server, so a production version should eventually use a hosted database and user accounts if multiple people need separate data.
