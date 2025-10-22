[![Language](https://img.shields.io/badge/lang-Python-blue.svg)]() [![License](https://img.shields.io/badge/license-MIT-green.svg)]() [![Status](https://img.shields.io/badge/status-active-success.svg)]()

# IT Helpdesk Ticket Tracker (CLI, SQLite)
A lightweight command-line tool to log and manage helpdesk tickets locally. Stores data in **SQLite** and supports **CSV export**.

## How to Run
```bash
python tracker.py new --title "Printer not connecting" --category Hardware --priority High --assignee "Andrew"
python tracker.py list
python tracker.py status --id 1 --status In-Progress
python tracker.py export --path tickets.csv
```
