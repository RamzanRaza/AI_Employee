"""
Approval System — Human-in-the-Loop Gate

For each plan in Plans/, creates an APPROVAL_*.md in Pending_Approval/
with the full plan content so the human reviewer can make an informed decision.

Skips plans that already have an approval anywhere in the pipeline.

To approve: move the file from Pending_Approval/ → Approved/
            (or use the MCP tool: approve_task)
"""

from pathlib import Path

PLANS   = Path("Plans")
PENDING = Path("Pending_Approval")
APPROVED = Path("Approved")
DONE    = Path("Done")

PENDING.mkdir(exist_ok=True)


def already_approved(plan_name: str) -> bool:
    approval_name = f"APPROVAL_{plan_name}"
    return (
        (PENDING  / approval_name).exists()
        or (APPROVED / approval_name).exists()
        or (DONE     / approval_name).exists()
    )


def create_approvals():
    for plan_file in PLANS.glob("*.md"):
        if already_approved(plan_file.name):
            print(f"[Approval] Already exists for {plan_file.name}, skipping.")
            continue

        plan_content = plan_file.read_text(encoding="utf-8", errors="ignore")

        # Check for sensitive actions flagged in the plan
        sensitive = any(
            kw in plan_content.lower()
            for kw in ["send", "email", "linkedin", "post", "publish", "notify", "message"]
        )
        warning = (
            "\n⚠️  SENSITIVE ACTION DETECTED — review carefully before approving.\n"
            if sensitive else ""
        )

        approval_file = PENDING / f"APPROVAL_{plan_file.name}"
        approval_file.write_text(
            f"""# Approval Required: {plan_file.stem}
{warning}
## Instructions
Review the plan below. To approve, move this file to the Approved/ folder.
You can also use the MCP tool: `approve_task("{approval_file.name}")`

---

{plan_content}
""",
            encoding="utf-8",
        )
        print(f"[Approval] Created: {approval_file.name}")


if __name__ == "__main__":
    create_approvals()
