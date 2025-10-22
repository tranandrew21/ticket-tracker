#!/usr/bin/env python3
"""
IT Helpdesk Ticket Tracker (SQLite)
------------------------------------------------------------
A lightweight command-line ticket management system for tracking
IT support issues such as hardware, software, or network incidents.

Features:
- Create, list, search, assign, and update ticket status
- Add notes and export tickets to CSV
- Simple local SQLite database (self-initializing)
- Built for quick, offline use by IT technicians
"""

import argparse, sqlite3, csv, os, sys, datetime as dt

# === DATABASE SETUP ===
# Database file is stored in the same directory as this script.
DB_PATH = os.path.join(os.path.dirname(__file__), "tickets.db")

# SQL schema automatically creates a 'tickets' table if it doesn't exist.
SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  priority TEXT NOT NULL,
  status TEXT NOT NULL,
  assignee TEXT,
  notes TEXT
);
"""

# === UTILITY FUNCTIONS ===

# Opens SQLite connection and ensures schema is initialized.
def get_conn():
  conn = sqlite3.connect(DB_PATH)
  conn.execute("PRAGMA journal_mode=WAL;")  # Improves concurrency and performance.
  conn.execute(SCHEMA)
  return conn

# Returns current timestamp formatted for database fields.
def now():
  return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# === CORE TICKET OPERATIONS ===

# Create a new ticket record in the database.
def create_ticket(a):
  with get_conn() as c:
    c.execute(
      """
      INSERT INTO tickets (created_at, updated_at, title, category, priority, status, assignee, notes)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      """,
      (now(), now(), a.title, a.category, a.priority, "Open", a.assignee, a.notes or "")
    )
    print("[+] Ticket created successfully.")

# List all existing tickets with basic info and status.
def list_tickets(a):
  for row in get_conn().execute(
    "SELECT id, created_at, title, category, priority, status, assignee FROM tickets ORDER BY id DESC"
  ):
    print(f"#{row[0]} [{row[5]}] {row[2]} | {row[3]} | {row[4]} | Assignee: {row[6]} | {row[1]}")

# Search tickets by keyword (title or notes).
def find_tickets(a):
  q = f"%{a.query}%"
  for row in get_conn().execute(
    "SELECT id, title, status, priority, category FROM tickets WHERE title LIKE ? OR notes LIKE ? ORDER BY id DESC",
    (q, q)
  ):
    print(f"#{row[0]} [{row[2]}] {row[1]} | {row[4]} | {row[3]}")

# Update the status of a specific ticket (e.g., Open -> Resolved).
def update_status(a):
  with get_conn() as c:
    c.execute(
      "UPDATE tickets SET status=?, updated_at=? WHERE id=?",
      (a.status, now(), a.id)
    )
    print(f"[+] Ticket #{a.id} status updated to: {a.status}")

# Append a note to an existing ticket’s notes field.
def add_note(a):
  with get_conn() as c:
    c.execute(
      "UPDATE tickets SET notes=COALESCE(notes,'')||?, updated_at=? WHERE id=?",
      ("\n" + a.note, now(), a.id)
    )
    print(f"[+] Note added to Ticket #{a.id}")

# Assign a ticket to a technician or staff member.
def assign(a):
  with get_conn() as c:
    c.execute(
      "UPDATE tickets SET assignee=?, updated_at=? WHERE id=?",
      (a.assignee, now(), a.id)
    )
    print(f"[+] Ticket #{a.id} assigned to {a.assignee}")

# Export all tickets to a CSV file for reporting or archival.
def export_csv(a):
  conn = get_conn()
  cur = conn.execute("SELECT * FROM tickets ORDER BY id ASC")
  with open(a.path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([d[0] for d in cur.description])  # Write header row
    w.writerows(cur.fetchall())
    print(f"[+] Exported all tickets to {a.path}")

# Generate and print ticket statistics by status and priority.
def stats(a):
  conn = get_conn()
  print("Status Counts:")
  for s, c in conn.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status"):
    print(f"- {s}: {c}")
  print("Priority Counts:")
  for p, c in conn.execute("SELECT priority, COUNT(*) FROM tickets GROUP BY priority"):
    print(f"- {p}: {c}")


# === ARGUMENT PARSER ===
# Defines all CLI commands (new, list, find, status, etc.)
def build_parser():
  p = argparse.ArgumentParser(description="IT Helpdesk Ticket Tracker (SQLite)")
  sub = p.add_subparsers(dest="cmd")

  # --- New Ticket ---
  new = sub.add_parser("new", help="Create a new support ticket")
  new.add_argument("--title", required=True, help="Short description of the issue")
  new.add_argument("--category", required=True, choices=["Hardware", "Software", "Network", "Account", "Other"])
  new.add_argument("--priority", default="Medium", choices=["Low", "Medium", "High", "Critical"])
  new.add_argument("--assignee", default="Unassigned")
  new.add_argument("--notes", default=None)
  new.set_defaults(func=create_ticket)

  # --- List Tickets ---
  lst = sub.add_parser("list", help="List all tickets")
  lst.set_defaults(func=list_tickets)

  # --- Find/Search ---
  fnd = sub.add_parser("find", help="Search tickets by keyword")
  fnd.add_argument("--query", required=True)
  fnd.set_defaults(func=find_tickets)

  # --- Update Status ---
  upd = sub.add_parser("status", help="Update ticket status")
  upd.add_argument("--id", type=int, required=True)
  upd.add_argument("--status", required=True, choices=["Open", "In-Progress", "Resolved", "Closed"])
  upd.set_defaults(func=update_status)

  # --- Add Note ---
  note = sub.add_parser("note", help="Add a note to a ticket")
  note.add_argument("--id", type=int, required=True)
  note.add_argument("--note", required=True)
  note.set_defaults(func=add_note)

  # --- Assign Ticket ---
  asg = sub.add_parser("assign", help="Assign a ticket to someone")
  asg.add_argument("--id", type=int, required=True)
  asg.add_argument("--assignee", required=True)
  asg.set_defaults(func=assign)

  # --- Export to CSV ---
  exp = sub.add_parser("export", help="Export all tickets to a CSV file")
  exp.add_argument("--path", required=True)
  exp.set_defaults(func=export_csv)

  # --- Show Statistics ---
  st = sub.add_parser("stats", help="Show ticket statistics")
  st.set_defaults(func=stats)

  return p


# === MAIN ENTRY POINT ===
def main():
  p = build_parser()
  a = p.parse_args()

  if not a.cmd:
    p.print_help()
    sys.exit(0)

  a.func(a)


if __name__ == "__main__":
  main()
