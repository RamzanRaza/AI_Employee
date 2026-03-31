"""
Gmail Watcher — polls Gmail via IMAP for unseen emails
and creates task files in Inbox/ for the pipeline.

Requires env vars: GMAIL_USER, GMAIL_APP_PASSWORD
Optional:         GMAIL_POLL_INTERVAL (seconds, default 60)
"""

import imaplib
import email
from email.header import decode_header
from pathlib import Path
import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

INBOX = Path("Inbox")
INBOX.mkdir(exist_ok=True)

GMAIL_USER         = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
POLL_INTERVAL      = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))


def _safe_name(text: str) -> str:
    return re.sub(r"[^\w\-_.]", "_", text)[:50]


def _decode(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)


def fetch_new_emails():
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[Gmail] ERROR: Set GMAIL_USER and GMAIL_APP_PASSWORD in .env")
        return

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")

        _, msg_nums = mail.search(None, "UNSEEN")
        ids = msg_nums[0].split()

        if not ids:
            print(f"[Gmail] No new emails.")
            mail.logout()
            return

        print(f"[Gmail] {len(ids)} new email(s) found.")

        for num in ids:
            _, data = mail.fetch(num, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decode subject
            raw_subject, enc = decode_header(msg.get("Subject") or "no_subject")[0]
            if isinstance(raw_subject, bytes):
                subject = raw_subject.decode(enc or "utf-8", errors="ignore")
            else:
                subject = raw_subject or "no_subject"

            sender = msg.get("From", "unknown")

            # Extract plain-text body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        body = _decode(payload)
                        break
            else:
                body = _decode(msg.get_payload(decode=True))

            filename = f"email_{_safe_name(subject)}.txt"
            task_file = INBOX / filename

            # Avoid overwriting an identical task
            if task_file.exists():
                print(f"[Gmail] Already exists, skipping: {filename}")
                mail.store(num, "+FLAGS", "\\Seen")
                continue

            task_file.write_text(
                f"Source: Gmail\nFrom: {sender}\nSubject: {subject}\n\n{body}",
                encoding="utf-8",
            )
            print(f"[Gmail] Task created: {filename}")

            mail.store(num, "+FLAGS", "\\Seen")

        mail.logout()

    except Exception as exc:
        print(f"[Gmail] Error: {exc}")


if __name__ == "__main__":
    print(f"[Gmail] Watcher started — polling every {POLL_INTERVAL}s")
    while True:
        fetch_new_emails()
        time.sleep(POLL_INTERVAL)
