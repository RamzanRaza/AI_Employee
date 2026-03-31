# Skill: Process Tasks (Reasoning Loop)

## Description
Read tasks from Needs_Action/, run a 3-step Claude reasoning loop,
and produce structured PLAN_*.md files in Plans/.

## Steps
1. **Understand** — Claude restates the task to confirm comprehension
2. **Consider**   — Claude identifies sensitive actions, missing info, urgency
3. **Plan**       — Claude produces a numbered execution plan

Each step builds on the previous via a multi-turn conversation (chain-of-thought).

## Trigger
- Automatic: orchestrator.py detects new file in Needs_Action/
- Scheduled: scheduler.py runs every 5 minutes
- Manual:    `python process_tasks.py`

## Rules
- Follow Company_Handbook
- Never delete files from Needs_Action/
- Skip tasks that already have a plan (idempotent)
- Flag sensitive actions (email, post, publish) in the Considerations step

## Output
Creates Plans/PLAN_<taskname>.md with sections:
  - Original Task
  - Step 1 — Task Understanding
  - Step 2 — Considerations & Risks
  - Step 3 — Execution Plan
  - Generated at (timestamp)
