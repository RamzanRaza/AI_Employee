"""
AI Employee MCP Server

Exposes the following tools to Claude Code (or any MCP client):

  send_email(to, subject, body)   — send email via Gmail SMTP
  post_to_linkedin(content)       — publish a post to LinkedIn
  list_pending_approvals()        — list tasks awaiting human sign-off
  approve_task(filename)          — move a task from Pending_Approval → Approved
  create_task(content, name?)     — drop a new task into Inbox
  get_pipeline_status()           — snapshot of all pipeline folder counts

Run with:   python mcp_server.py
Or via MCP: configure in .claude/settings.json (see README)
"""

import os
import smtplib
import datetime
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("AI Employee")

BASE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Email tool
# ---------------------------------------------------------------------------

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail SMTP.

    Args:
        to:      Recipient email address.
        subject: Email subject line.
        body:    Plain-text email body.
    """
    user     = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not user or not password:
        return "Error: GMAIL_USER or GMAIL_APP_PASSWORD not set in .env"

    try:
        msg = MIMEMultipart()
        msg["From"]    = user
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(user, password)
            server.sendmail(user, to, msg.as_string())

        return f"Email sent to {to} — subject: {subject}"
    except Exception as exc:
        return f"Error sending email: {exc}"


# ---------------------------------------------------------------------------
# LinkedIn tool
# ---------------------------------------------------------------------------

@mcp.tool()
def post_to_linkedin(content: str) -> str:
    """Publish a post to LinkedIn.

    Args:
        content: The text content to post.
    """
    token      = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")

    if not token or not person_urn:
        return "Error: LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN not set in .env"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=payload,
            timeout=15,
        )
        if resp.status_code in (200, 201):
            post_id = resp.headers.get("X-RestLi-Id", "unknown")
            return f"Posted to LinkedIn. Post ID: {post_id}"
        return f"LinkedIn error {resp.status_code}: {resp.text[:300]}"
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Pipeline management tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_pending_approvals() -> str:
    """List all tasks currently waiting for human approval."""
    pending = BASE / "Pending_Approval"
    files = sorted(pending.glob("*"))
    if not files:
        return "No pending approvals."
    lines = [f.name for f in files]
    return "\n".join(lines)


@mcp.tool()
def approve_task(filename: str) -> str:
    """Approve a task — moves it from Pending_Approval/ to Approved/.

    Args:
        filename: The exact filename shown by list_pending_approvals.
    """
    src  = BASE / "Pending_Approval" / filename
    dest = BASE / "Approved" / filename

    if not src.exists():
        return f"Not found in Pending_Approval: {filename}"

    src.rename(dest)
    return f"Approved: {filename} — pipeline will execute it shortly."


@mcp.tool()
def create_task(task_content: str, task_name: str = "") -> str:
    """Create a new task by placing it in Inbox/ for the pipeline to pick up.

    Args:
        task_content: What the task is (plain text).
        task_name:    Optional filename (e.g. 'draft_proposal.txt').
                      Defaults to a timestamped name.
    """
    inbox = BASE / "Inbox"
    inbox.mkdir(exist_ok=True)
    name = task_name or f"task_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    task_file = inbox / name
    task_file.write_text(task_content, encoding="utf-8")
    return f"Task created: {name}"


@mcp.tool()
def get_pipeline_status() -> str:
    """Return a snapshot of how many files are in each pipeline stage."""
    folders = [
        "Inbox", "Needs_Action", "Plans",
        "Pending_Approval", "Approved", "Done",
    ]
    lines = []
    for name in folders:
        folder = BASE / name
        count  = len(list(folder.glob("*"))) if folder.exists() else 0
        lines.append(f"{name:<20} {count} file(s)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
