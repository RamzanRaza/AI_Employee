from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
import time

INBOX = Path("Inbox")
NEEDS_ACTION = Path("Needs_Action")

INBOX.mkdir(exist_ok=True)
NEEDS_ACTION.mkdir(exist_ok=True)

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        dest = NEEDS_ACTION / src.name

        shutil.copy(src, dest)

        print(f"Moved to Needs_Action: {src.name}")

observer = Observer()
observer.schedule(Handler(), str(INBOX), recursive=False)
observer.start()

print("Watcher running...")

while True:
    time.sleep(1)