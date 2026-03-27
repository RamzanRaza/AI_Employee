from pathlib import Path
import datetime

APPROVED = Path("Approved")
DONE = Path("Done")
LOG_DIR = Path("Logs")
LOG_FILE = LOG_DIR / "log.txt"

# ✅ Ensure folders exist
DONE.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

def execute():
    for file in APPROVED.glob("*"):
        print(f"Executing action for {file.name}")

        # ✅ Write log
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} Executed {file.name}\n")

        # ✅ Move to Done
        file.rename(DONE / file.name)

if __name__ == "__main__":
    execute()