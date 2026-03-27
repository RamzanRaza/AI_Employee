from pathlib import Path

PLANS = Path("Plans")
PENDING = Path("Pending_Approval")

PENDING.mkdir(exist_ok=True)

def create_approvals():
    for file in PLANS.glob("*"):
        approval_file = PENDING / f"APPROVAL_{file.name}"

        approval_file.write_text(f"""
Approval Required for:
{file.name}

Move this file to Approved/ to execute
""")

        print(f"Approval created for {file.name}")

if __name__ == "__main__":
    create_approvals()