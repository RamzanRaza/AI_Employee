from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
import time

INBOX = Path("Inbox")
NEEDS_ACTION = Path("Needs_Action")

INBOX.mkdir(exist_ok=True)
NEEDS_ACTION.mkdir(exist_ok=True)

# Track processed files
processed_files = {}

class Handler(FileSystemEventHandler):

    def process_file(self, src):
        if not src.exists():
            return

        size = src.stat().st_size

        # Skip empty files
        if size == 0:
            return

        dest = NEEDS_ACTION / src.name

        shutil.copy2(src, dest)

        processed_files[src] = size

        print(f"Updated file with content: {src.name}")

    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        print(f"Created: {src.name}")

        # Do nothing yet (file likely empty)

    def on_modified(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)

        if not src.exists():
            return

        size = src.stat().st_size

        # Only update if:
        # 1. File has content
        # 2. Size changed (new content)
        if size > 0 and processed_files.get(src) != size:
            time.sleep(0.5)  # small delay
            self.process_file(src)


observer = Observer()
observer.schedule(Handler(), str(INBOX), recursive=False)
observer.start()

print("Smart watcher running...")

while True:
    time.sleep(1)