from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import subprocess
import time

# Folders
NEEDS = Path("Needs_Action")
PLANS = Path("Plans")
APPROVED = Path("Approved")

print("🚀 Event-driven AI Employee started...\n")

# -----------------------------
# HANDLERS
# -----------------------------

class NeedsActionHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        print(f"[Trigger] New task detected: {event.src_path}")
        print("[AI] Running process_tasks...\n")
        subprocess.run(["python", "process_tasks.py"])


class PlansHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        print(f"[Trigger] New plan created: {event.src_path}")
        print("[Approval] Generating approval...\n")
        subprocess.run(["python", "approval_system.py"])


class ApprovedHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        print(f"[Trigger] Approved task detected: {event.src_path}")
        print("[Action] Executing action...\n")
        subprocess.run(["python", "action.py"])


# -----------------------------
# OBSERVER SETUP
# -----------------------------

observer = Observer()

observer.schedule(NeedsActionHandler(), str(NEEDS), recursive=False)
observer.schedule(PlansHandler(), str(PLANS), recursive=False)
observer.schedule(ApprovedHandler(), str(APPROVED), recursive=False)

observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()