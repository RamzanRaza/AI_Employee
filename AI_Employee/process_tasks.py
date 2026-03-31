"""
Process Tasks — Claude Reasoning Loop

For each new task in Needs_Action/, runs a 3-step reasoning loop:
  1. Understand  — restate the task to confirm comprehension
  2. Consider    — identify risks, sensitive actions, missing info
  3. Plan        — produce a numbered execution plan

Outputs PLAN_<task>.md into Plans/.
Skips tasks that already have a plan.
"""

from pathlib import Path
import anthropic
import datetime

NEEDS = Path("Needs_Action")
PLANS = Path("Plans")
PLANS.mkdir(exist_ok=True)

SYSTEM = (
    "You are a professional AI employee. "
    "Follow the Company Handbook: always be polite, ask before sending anything externally, "
    "handle urgent tasks first."
)

client = anthropic.Anthropic()


def reasoning_loop(task_content: str) -> tuple[str, str, str]:
    """Run 3-step reasoning. Returns (understanding, considerations, plan)."""

    # ── Step 1: Understand ────────────────────────────────────────────────
    messages = [{"role": "user", "content": f"Task: {task_content}"}]

    r1 = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        system=SYSTEM + " Restate the task in your own words in 2-3 sentences to confirm understanding. Be concise.",
        messages=messages,
    )
    understanding = r1.content[0].text.strip()

    # ── Step 2: Consider ──────────────────────────────────────────────────
    messages += [
        {"role": "assistant", "content": understanding},
        {"role": "user", "content": (
            "Now identify: (a) any sensitive actions (sending emails, posting publicly, "
            "contacting people), (b) missing information needed, (c) urgency level."
        )},
    ]

    r2 = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=400,
        system=SYSTEM,
        messages=messages,
    )
    considerations = r2.content[0].text.strip()

    # ── Step 3: Plan ──────────────────────────────────────────────────────
    messages += [
        {"role": "assistant", "content": considerations},
        {"role": "user", "content": (
            "Based on your understanding and considerations, write the final numbered "
            "execution plan. Be specific and actionable."
        )},
    ]

    r3 = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=800,
        system=SYSTEM,
        messages=messages,
    )
    plan = r3.content[0].text.strip()

    return understanding, considerations, plan


def process():
    tasks = [f for f in NEEDS.glob("*") if f.is_file()]

    if not tasks:
        print("[process_tasks] Nothing to process.")
        return

    for file in tasks:
        plan_file = PLANS / f"PLAN_{file.stem}.md"

        if plan_file.exists():
            print(f"[process_tasks] Plan already exists for {file.name}, skipping.")
            continue

        content = file.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            print(f"[process_tasks] Skipping empty file: {file.name}")
            continue

        print(f"[Reasoning Loop] Step 1/3 — Understanding: {file.name}")
        print(f"[Reasoning Loop] Step 2/3 — Considering risks...")
        print(f"[Reasoning Loop] Step 3/3 — Generating plan...")

        understanding, considerations, plan = reasoning_loop(content)

        plan_file.write_text(
            f"""# Plan for {file.name}

## Original Task
{content}

## Step 1 — Task Understanding
{understanding}

## Step 2 — Considerations & Risks
{considerations}

## Step 3 — Execution Plan
{plan}

## Generated at
{datetime.datetime.now()}
""",
            encoding="utf-8",
        )

        print(f"[Reasoning Loop] Plan created: {plan_file.name}")


if __name__ == "__main__":
    process()
