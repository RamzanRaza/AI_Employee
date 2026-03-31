"""
AI Employee Scheduler

Runs recurring jobs on a cron-like schedule using the `schedule` library.

Default schedule:
  Every 1 hour      — check Gmail for new emails
  Every 5 minutes   — process any pending tasks in Needs_Action
  Every Monday 9am  — generate + post to LinkedIn
  Every day   8am   — print pipeline status summary

Override intervals via .env:
  SCHEDULER_GMAIL_INTERVAL_MINUTES   (default 60)
  SCHEDULER_TASKS_INTERVAL_MINUTES   (default 5)
  SCHEDULER_LINKEDIN_DAY             (default monday)
  SCHEDULER_LINKEDIN_TIME            (default 09:00)

Run: python scheduler.py
"""

import os
import subprocess
import datetime
from pathlib import Path
from dotenv import load_dotenv
import schedule
import time

load_dotenv()

BASE     = Path(__file__).parent
LOG_DIR  = BASE / "Logs"
LOG_FILE = LOG_DIR / "scheduler.log"
LOG_DIR.mkdir(exist_ok=True)

GMAIL_INTERVAL    = int(os.getenv("SCHEDULER_GMAIL_INTERVAL_MINUTES",  "60"))
TASKS_INTERVAL    = int(os.getenv("SCHEDULER_TASKS_INTERVAL_MINUTES",   "5"))
LINKEDIN_DAY      = os.getenv("SCHEDULER_LINKEDIN_DAY",   "monday")
LINKEDIN_TIME     = os.getenv("SCHEDULER_LINKEDIN_TIME",  "09:00")


def _log(msg: str):
    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _run(script: str, *args):
    cmd = ["python", script, *args]
    result = subprocess.run(cmd, cwd=str(BASE), capture_output=True, text=True)
    if result.stdout.strip():
        _log(result.stdout.strip())
    if result.stderr.strip():
        _log(f"[STDERR] {result.stderr.strip()[:300]}")


# ---------------------------------------------------------------------------
# Job definitions
# ---------------------------------------------------------------------------

def job_gmail():
    _log("=== Gmail check ===")
    _run("gmail_watcher.py")


def job_process_tasks():
    _log("=== Process pending tasks ===")
    _run("process_tasks.py")


def job_linkedin_post():
    _log("=== LinkedIn auto-post ===")
    _run("linkedin_watcher.py", "post")


def job_pipeline_status():
    _log("=== Pipeline Status ===")
    folders = ["Inbox", "Needs_Action", "Plans", "Pending_Approval", "Approved", "Done"]
    for name in folders:
        count = len(list((BASE / name).glob("*"))) if (BASE / name).exists() else 0
        _log(f"  {name:<20} {count} file(s)")


# ---------------------------------------------------------------------------
# Schedule wiring
# ---------------------------------------------------------------------------

schedule.every(GMAIL_INTERVAL).minutes.do(job_gmail)
schedule.every(TASKS_INTERVAL).minutes.do(job_process_tasks)
schedule.every().day.at("08:00").do(job_pipeline_status)

# LinkedIn post: schedule on the configured weekday at the configured time
_linkedin_scheduler = getattr(schedule.every(), LINKEDIN_DAY)
_linkedin_scheduler.at(LINKEDIN_TIME).do(job_linkedin_post)

_log("Scheduler started.")
_log(f"  Gmail check      : every {GMAIL_INTERVAL} minute(s)")
_log(f"  Process tasks    : every {TASKS_INTERVAL} minute(s)")
_log(f"  LinkedIn post    : every {LINKEDIN_DAY} at {LINKEDIN_TIME}")
_log(f"  Pipeline status  : every day at 08:00")

# Run all jobs once immediately on startup
job_pipeline_status()

while True:
    schedule.run_pending()
    time.sleep(15)
