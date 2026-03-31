"""
Action Executor

Processes files in Approved/, calls Claude to execute the task,
and writes the result to Done/.

Sensitive-action detection:
  - If the task involves sending an email with a clear recipient
    → sends it via Gmail SMTP (mcp_server.send_email)
  - If the task involves posting to LinkedIn
    → posts via LinkedIn API (linkedin_watcher.generate_and_post)
  - All other tasks → Claude generates the output and saves it to Done/
"""

from pathlib import Path
import anthropic
import datetime
import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

APPROVED = Path("Approved")
NEEDS    = Path("Needs_Action")
PLANS    = Path("Plans")
DONE     = Path("Done")
LOG_DIR  = Path("Logs")
LOG_FILE = LOG_DIR / "log.txt"

DONE.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic()

SYSTEM = (
    "You are a professional AI employee. Execute the given task completely and accurately. "
    "Follow the Company Handbook: always be polite, ask before sending anything externally, "
    "handle urgent tasks first."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_task_content(approval_filename: str) -> tuple[str, str | None]:
    """Return (task_stem, task_content) by tracing back from the approval filename."""
    stem = approval_filename.removeprefix("APPROVAL_PLAN_").removesuffix(".md")

    for ext in (".txt", ".md", ""):
        task_file = NEEDS / f"{stem}{ext}"
        if task_file.exists():
            return stem, task_file.read_text(encoding="utf-8", errors="ignore").strip()

    # Fallback: extract from the plan file
    plan_file = PLANS / f"PLAN_{stem}.md"
    if plan_file.exists():
        text = plan_file.read_text(encoding="utf-8", errors="ignore")
        marker = "## Original Task"
        if marker in text:
            snippet = text.split(marker, 1)[1].split("##")[0].strip()
            return stem, snippet

    return stem, None


def detect_action_type(task_content: str) -> str:
    lower = task_content.lower()
    if re.search(r"\b(send|write|draft).{0,30}(email|mail)\b", lower):
        return "email"
    if re.search(r"\b(post|publish|share).{0,30}linkedin\b", lower):
        return "linkedin"
    return "general"


def extract_email_recipient(task_content: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", task_content)
    return match.group(0) if match else None


# ---------------------------------------------------------------------------
# Executors
# ---------------------------------------------------------------------------

def execute_general(task_name: str, task_content: str) -> str:
    """Call Claude to produce the task output."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM,
        messages=[{"role": "user", "content": task_content}],
    )
    return response.content[0].text.strip()


def execute_email(task_name: str, task_content: str):
    """Generate an email via Claude. If recipient found, send it; otherwise save draft."""
    # Generate the email content
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": task_content}],
    )
    email_body = response.content[0].text.strip()

    recipient = extract_email_recipient(task_content)
    gmail_user     = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if recipient and gmail_user and gmail_password:
        try:
            msg = MIMEMultipart()
            msg["From"]    = gmail_user
            msg["To"]      = recipient
            msg["Subject"] = f"Re: {task_name}"
            msg.attach(MIMEText(email_body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, recipient, msg.as_string())

            print(f"[Action] Email sent to {recipient}")
            return email_body, f"Sent to: {recipient}"
        except Exception as exc:
            print(f"[Action] Email send failed: {exc} — saving draft instead.")
            return email_body, f"Draft (send failed: {exc})"
    else:
        reason = "no recipient found in task" if not recipient else "Gmail credentials not set"
        print(f"[Action] Saving email draft ({reason}).")
        return email_body, f"Draft — {reason}"


def execute_linkedin(task_name: str, task_content: str):
    """Generate LinkedIn post via Claude and publish it."""
    try:
        from linkedin_watcher import generate_and_post
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=600,
            system="You are a professional LinkedIn content writer for a B2B AI-services company.",
            messages=[{"role": "user", "content": task_content}],
        )
        post_content = response.content[0].text.strip()
        success = generate_and_post(post_content)
        status = "Posted to LinkedIn" if success else "Post failed — saved draft"
        return post_content, status
    except Exception as exc:
        result = execute_general(task_name, task_content)
        return result, f"LinkedIn post generation failed ({exc}) — draft saved"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def execute():
    files = list(APPROVED.glob("*"))
    if not files:
        print("[Action] Nothing in Approved/.")
        return

    for file in files:
        task_name, task_content = get_task_content(file.name)

        if not task_content:
            print(f"[Action] WARNING: No task content found for {file.name} — moving as-is.")
            file.rename(DONE / file.name)
            continue

        action_type = detect_action_type(task_content)
        print(f"[Action] Executing '{task_name}' (type: {action_type})")

        if action_type == "email":
            result, status = execute_email(task_name, task_content)
            output = f"# {task_name}\n\n## Task\n{task_content}\n\n## Email Draft\n{result}\n\n## Status\n{status}\n\n## Completed at\n{datetime.datetime.now()}\n"

        elif action_type == "linkedin":
            result, status = execute_linkedin(task_name, task_content)
            output = f"# {task_name}\n\n## Task\n{task_content}\n\n## Post Content\n{result}\n\n## Status\n{status}\n\n## Completed at\n{datetime.datetime.now()}\n"

        else:
            result = execute_general(task_name, task_content)
            output = f"# {task_name}\n\n## Task\n{task_content}\n\n## Result\n{result}\n\n## Completed at\n{datetime.datetime.now()}\n"

        output_file = DONE / f"{task_name}.md"
        output_file.write_text(output, encoding="utf-8")

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} Executed {file.name} -> {output_file.name}\n")

        file.rename(DONE / file.name)
        print(f"[Action] Done: {output_file.name}")


if __name__ == "__main__":
    execute()
