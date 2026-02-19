# NFL Draft Scout Assistant

NFL Draft Scout Assistant is a local Flask + SQLite web app for scouting prospects, comparing ranking boards, and managing your own Big Board workflow.

## Packaged App Quick Start (Windows Users)
If you want to download the packaged version of the app it can be found here:

https://tinyurl.com/2bujkf2f

If you downloaded the packaged build, you only need the files in the release folder/zip.

1. Extract `ScoutingApp-Windows.zip`.
2. Double-click `ScoutingApp.exe`.
3. Wait for your browser to open `http://127.0.0.1:5000`.
4. Open the **Settings** tab and run these buttons in order:
  - **Import 2026 Consensus Board**
  - **Import Tankathon Board**
  - **Recalculate Player Rankings**
5. (Optional) Run **Refresh Downloaded Logos** and/or import additional boards.

After that, use Search / Randomizer / Big Board / Watch List normally. When finished, click **Stop App** in the top-right of the app.

Notes:
- First launch and first import can take a little time.
- Board import buttons require internet access.

## Features

- Multi-source rankings support:
  - Tankathon import
  - Consensus 2026 import
  - NFLMockDraftDatabase URL import
  - TXT board import + normalization
- Configurable board weighting and primary board selection
- Duplicate player merge by normalized names
- Search + filters by name, school, position, and scouted status
- Big Board management:
  - Overall and positional boards
  - Add/remove/reorder players
  - Auto-sort by grades
- Player scouting workflow:
  - Notes, games watched, grade systems
  - Editable profile fields and stats
- Export normalized boards to TXT

## Tech Stack

- Backend: Flask
- Database: SQLite
- Frontend: Vanilla JavaScript + HTML/CSS
- Scraping: requests + BeautifulSoup

## Project Structure

- `app.py`: Flask routes and API endpoints
- `database.py`: persistence and ranking logic
- `consensus_scraper.py`: consensus + URL board scraping
- `webscraper.py`: Tankathon fetch/export script
- `templates/index.html`: main app UI
- `static/js/app.js`: app orchestration layer
- `static/js/api-client.js`: shared API request utilities
- `static/js/ui-feedback.js`: toast + confirm UI utilities
- `static/js/bigboard-controller.js`: Big Board feature module
- `static/js/player-report-controller.js`: player report/profile module
- `docs/performance-notes.md`: DB index/query notes
- `docs/frontend-organization.md`: frontend module organization notes

## Quick Start

### 1) Create and activate virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install flask requests beautifulsoup4
```

### 3) Run the app

```powershell
python app.py
```

Then open:

`http://127.0.0.1:5000`

## Data / Database Notes

- Default DB file: `scout_database.db`
- Tables and indexes are initialized/updated on app startup in `ScoutDatabase.init_database()`.
- Rank recalculation and positional-rank updates are run after board imports and selected maintenance operations.

## App Workflows

### Ranking Import & Normalization

Use **Settings > App Tools** and **Import / Export Big Boards** to:

- Import Tankathon board
- Import Consensus 2026 board
- Import NFLMockDraftDatabase board URL
- Import TXT boards in bulk with equal/weighted mode
- Recalculate player rankings

### Big Board Management

Use **Big Board** tab to:

- Switch between Overall and Position boards
- Search/add players from DB
- Drag and drop to reorder
- Auto-sort by current grades

### Player Scouting

Open a player report from Search/Randomizer/Big Board to:

- Mark or unmark as scouted
- Save notes and games watched
- Apply primary/secondary grading systems
- Edit profile fields and stats JSON via builder rows

## Testing

Run tests with:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Current tests cover core ranking/import invariants and duplicate merge idempotency.

## Windows Packaging (.exe + .zip)

Build a distributable one-file executable and release zip:

```powershell
.\build_windows_package.ps1
```

This produces:

- `release/ScoutingApp/ScoutingApp.exe`
- `release/ScoutingApp/RUN.txt`
- `release/ScoutingApp-Windows.zip`

The executable uses `launcher.py` + Waitress to start the app on `http://127.0.0.1:5000` and opens your browser automatically.

To stop the running packaged app, use the top-right **Stop App** button in the web UI.

## Troubleshooting

- If board imports seem stale, run **Recalculate Player Rankings**.
- If rank pills are cluttered, toggle board visibility in Settings.
- If logos are missing, run **Refresh Downloaded Logos**.

## Roadmap (Suggested Next Refactors)

- Extract settings logic from `app.js` into a dedicated controller module
- Add frontend smoke tests for Big Board and player report flows
- Add API-level tests for critical settings endpoints
