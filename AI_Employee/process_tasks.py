from pathlib import Path
import anthropic
import datetime

NEEDS = Path("Needs_Action")
PLANS = Path("Plans")

PLANS.mkdir(exist_ok=True)

client = anthropic.Anthropic()

def process():
    for file in NEEDS.glob("*"):
        plan_file = PLANS / f"PLAN_{file.stem}.md"

        if plan_file.exists():
            print(f"Plan already exists for {file.name}, skipping.")
            continue

        content = file.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            continue

        print(f"[Claude] Planning task: {file.name}")

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system="You are an AI employee assistant. Create a brief, actionable execution plan for the given task.",
            messages=[{"role": "user", "content": f"Task: {content}\n\nCreate a concise step-by-step plan to execute this task."}]
        )

        plan_content = response.content[0].text

        plan_file.write_text(f"""# Plan for {file.name}

## Original Task
{content}

## Execution Plan
{plan_content}

## Generated at
{datetime.datetime.now()}
""", encoding="utf-8")
        print(f"Plan created for {file.name}")

if __name__ == "__main__":
    process()
