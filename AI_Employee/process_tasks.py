from pathlib import Path
import datetime

NEEDS = Path("Needs_Action")
PLANS = Path("Plans")

PLANS.mkdir(exist_ok=True)

def process():
    for file in NEEDS.glob("*"):
        content = file.read_text()

        plan_file = PLANS / f"PLAN_{file.stem}.md"

        plan_file.write_text(f"""
# Plan for {file.name}

## Task Understanding
{content}

## Steps
- Analyze request
- Decide action
- Prepare response
- Request approval

## Generated at
{datetime.datetime.now()}
""")

        print(f"Plan created for {file.name}")

if __name__ == "__main__":
    process()