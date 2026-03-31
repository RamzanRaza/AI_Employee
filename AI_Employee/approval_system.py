from pathlib import Path

PLANS = Path("Plans")
PENDING = Path("Pending_Approval")

PENDING.mkdir(exist_ok=True)

DONE = Path("Done")
APPROVED = Path("Approved")

def create_approvals():
    for file in PLANS.glob("*"):
        approval_file = PENDING / f"APPROVAL_{file.name}"

        # Skip if approval already exists anywhere in the pipeline
        if (approval_file.exists()
                or (APPROVED / f"APPROVAL_{file.name}").exists()
                or (DONE / f"APPROVAL_{file.name}").exists()):
            print(f"Approval already exists for {file.name}, skipping.")
            continue

        approval_file.write_text(f"""
Approval Required for:
{file.name}

Move this file to Approved/ to execute
""")

        print(f"Approval created for {file.name}")

if __name__ == "__main__":
    create_approvals()