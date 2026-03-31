"""
LinkedIn Watcher — two modes:

  1. Watch mode (default):  polls LinkedIn notifications/messages via API
                            and creates task files in Inbox/
  2. Post mode:             generates a business post via Claude and
                            publishes it to LinkedIn automatically

Usage:
  python linkedin_watcher.py              # watch mode
  python linkedin_watcher.py post         # generate + post immediately
  python linkedin_watcher.py post "topic" # post on a specific topic

Requires env vars:
  LINKEDIN_ACCESS_TOKEN   — OAuth2 bearer token
  LINKEDIN_PERSON_URN     — e.g. urn:li:person:XXXXXXXXX
Optional:
  LINKEDIN_POLL_INTERVAL  — seconds between notification polls (default 300)
"""

import os
import sys
import time
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv()

INBOX  = Path("Inbox")
DONE   = Path("Done")
INBOX.mkdir(exist_ok=True)
DONE.mkdir(exist_ok=True)

LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN   = os.getenv("LINKEDIN_PERSON_URN")
POLL_INTERVAL         = int(os.getenv("LINKEDIN_POLL_INTERVAL", "300"))

client = anthropic.Anthropic()

HEADERS = lambda: {
    "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "X-Restli-Protocol-Version": "2.0.0",
}


# ---------------------------------------------------------------------------
# Watch mode
# ---------------------------------------------------------------------------

def check_notifications():
    if not LINKEDIN_ACCESS_TOKEN:
        print("[LinkedIn] ERROR: Set LINKEDIN_ACCESS_TOKEN in .env")
        return

    try:
        # Poll recent shares/mentions via LinkedIn UGC API
        url = "https://api.linkedin.com/v2/shares?q=owners&owners={urn}&sharesPerOwner=5".format(
            urn=LINKEDIN_PERSON_URN
        )
        resp = requests.get(url, headers=HEADERS(), timeout=10)

        if resp.status_code == 401:
            print("[LinkedIn] Token expired or invalid. Refresh LINKEDIN_ACCESS_TOKEN.")
            return
        if resp.status_code != 200:
            print(f"[LinkedIn] API warning: {resp.status_code}")
            return

        data = resp.json()
        for item in data.get("elements", []):
            item_id = item.get("id", "")
            task_file = INBOX / f"linkedin_{item_id}.txt"
            if not task_file.exists():
                task_file.write_text(
                    f"Source: LinkedIn\nType: Share\nID: {item_id}\n\n{item}",
                    encoding="utf-8",
                )
                print(f"[LinkedIn] Task created: {task_file.name}")

    except Exception as exc:
        print(f"[LinkedIn] Watch error: {exc}")


# ---------------------------------------------------------------------------
# Post mode
# ---------------------------------------------------------------------------

def generate_and_post(topic: str = None) -> bool:
    """Generate a LinkedIn post via Claude and publish it. Returns True on success."""
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
        print("[LinkedIn] ERROR: Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN in .env")
        return False

    prompt = topic if topic else (
        "Generate a professional LinkedIn post for a B2B AI-services company. "
        "Goal: attract new business clients. Keep it under 280 words, use 2-3 relevant "
        "emojis, include a clear call-to-action. Do not include a subject line."
    )

    print("[Claude] Generating LinkedIn post content...")
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=600,
        system=(
            "You are a professional LinkedIn content writer for a B2B AI-services company. "
            "Write compelling, concise posts that showcase AI expertise and drive inbound leads."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    post_content = response.content[0].text.strip()
    print(f"[LinkedIn] Post preview:\n{post_content[:120]}...\n")

    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=HEADERS(),
            json=payload,
            timeout=15,
        )
    except Exception as exc:
        print(f"[LinkedIn] Request error: {exc}")
        return False

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("X-RestLi-Id", "unknown")
        print(f"[LinkedIn] Posted. ID: {post_id}")

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = DONE / f"linkedin_post_{ts}.md"
        log_file.write_text(
            f"# LinkedIn Post\n\n{post_content}\n\n## Posted at\n{datetime.datetime.now()}\n",
            encoding="utf-8",
        )
        return True
    else:
        print(f"[LinkedIn] Post failed: {resp.status_code} — {resp.text[:300]}")
        return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "post":
        topic = " ".join(sys.argv[2:]) or None
        generate_and_post(topic)
    else:
        print(f"[LinkedIn] Watcher started — polling every {POLL_INTERVAL}s")
        while True:
            check_notifications()
            time.sleep(POLL_INTERVAL)
