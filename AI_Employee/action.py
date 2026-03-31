from pathlib import Path
import anthropic
import datetime

APPROVED = Path("Approved")
NEEDS = Path("Needs_Action")
PLANS = Path("Plans")
DONE = Path("Done")
LOG_DIR = Path("Logs")
LOG_FILE = LOG_DIR / "log.txt"

DONE.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic()

def get_task_content(approval_filename):
    """Derive original task name and content from the approval file name.
    APPROVAL_PLAN_mail.md -> looks for mail.txt / mail.md in Needs_Action"""
    stem = approval_filename.removeprefix("APPROVAL_PLAN_").removesuffix(".md")

    for ext in [".txt", ".md", ""]:
        task_file = NEEDS / f"{stem}{ext}"
        if task_file.exists():
            return stem, task_file.read_text(encoding="utf-8", errors="ignore").strip()

    # Fallback: pull the original task section out of the plan file
    plan_file = PLANS / f"PLAN_{stem}.md"
    if plan_file.exists():
        text = plan_file.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if line.startswith("## Original Task"):
                idx = text.find("## Original Task") + len("## Original Task")
                snippet = text[idx:].split("##")[0].strip()
                return stem, snippet

    return stem, None

def execute():
    for file in APPROVED.glob("*"):
        task_name, task_content = get_task_content(file.name)

        if not task_content:
            print(f"[Warning] Could not find task content for {file.name}, moving to Done as-is.")
            file.rename(DONE / file.name)
            continue

        print(f"[Claude] Executing task: {task_name}")

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=(
                "You are a professional AI employee. Execute the given task completely and "
                "professionally. Follow the Company Handbook: always be polite, ask before "
                "sending anything, handle urgent tasks first."
            ),
            messages=[{"role": "user", "content": task_content}]
        )

        result = response.content[0].text

        output_file = DONE / f"{task_name}.md"
        output_file.write_text(f"""# {task_name}

## Task
{task_content}

## Result
{result}

## Completed at
{datetime.datetime.now()}
""", encoding="utf-8")

        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} Executed {file.name} -> {output_file.name}\n")

        file.rename(DONE / file.name)
        print(f"Done: {output_file.name}")

if __name__ == "__main__":
    execute()
