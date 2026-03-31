# AI Employee — Architecture Overview

An event-driven AI workflow system built on an Obsidian vault, implementing a
human-in-the-loop pipeline where tasks flow from multiple input sources through
staged folders to automated execution — powered by Claude.

---

## Folder Structure

```
AI_Employee/
├── Inbox/                    # All watchers drop tasks here
├── Needs_Action/             # Validated tasks awaiting planning
├── Plans/                    # Claude reasoning-loop plans (PLAN_*.md)
├── Pending_Approval/         # Plans awaiting human sign-off
├── Approved/                 # Human-approved tasks ready to execute
├── Done/                     # Completed output + archived approvals
├── Logs/                     # log.txt + scheduler.log
│
│── Watchers (run continuously in separate terminals)
├── file_watcher.py           # Watches Inbox/ for new files
├── gmail_watcher.py          # Polls Gmail IMAP for unread emails
├── linkedin_watcher.py       # Polls LinkedIn notifications + auto-posts
│
│── Core Pipeline
├── orchestrator.py           # Event hub — triggers pipeline stages
├── process_tasks.py          # Claude 3-step reasoning loop → Plans/
├── approval_system.py        # Creates human-review requests → Pending_Approval/
├── action.py                 # Executes approved tasks via Claude + APIs
│
│── Automation
├── scheduler.py              # Cron-like scheduler for recurring jobs
├── mcp_server.py             # MCP server — exposes tools to Claude Code
│
│── Skills (Agent Skill definitions)
├── SKILL_process_tasks.md    # Reasoning loop skill
├── SKILL_gmail_watcher.md    # Gmail watcher skill
├── SKILL_linkedin_post.md    # LinkedIn auto-post skill
├── SKILL_mcp_server.md       # MCP server skill
├── SKILL_scheduler.md        # Scheduler skill
│
│── Config & Docs
├── .env.example              # All environment variables (copy → .env)
├── requirements.txt          # Python dependencies
├── Company_Handbook.md       # Policy rules enforced by all agents
└── Dashboard.md              # Task status dashboard
```

---

## Full Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT SOURCES                        │
│  file_watcher.py   gmail_watcher.py   linkedin_watcher  │
│   (file system)       (IMAP poll)       (API poll)      │
└──────────────────────────┬──────────────────────────────┘
                           │ drops .txt files
                           ▼
                        Inbox/
                           │
                    file_watcher.py
                    (copies to next stage)
                           │
                           ▼
                     Needs_Action/
                           │
              orchestrator.py detects file
                           │
                           ▼
              process_tasks.py (Claude Reasoning Loop)
                ┌──────────────────────────────┐
                │  Step 1: Understand task      │
                │  Step 2: Identify risks       │
                │  Step 3: Generate plan        │
                └──────────────────────────────┘
                           │
                           ▼
                        Plans/
                           │
              orchestrator.py detects plan
                           │
                           ▼
              approval_system.py
              (includes full plan + sensitive-action warning)
                           │
                           ▼
                   Pending_Approval/
                           │
                    [HUMAN REVIEWS]
                    Move file to Approved/
                    or use MCP: approve_task()
                           │
                           ▼
                        Approved/
                           │
              orchestrator.py detects approval
                           │
                           ▼
              action.py (Claude + API execution)
                ┌──────────────────────────────┐
                │  email task  → Gmail SMTP     │
                │  linkedin    → LinkedIn API   │
                │  general     → Claude output  │
                └──────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                 Done/         Logs/
              (result.md)    (log.txt)
```

---

## Watcher Scripts

| Script                | Source           | Method            | Output          |
|-----------------------|------------------|-------------------|-----------------|
| `file_watcher.py`     | Local filesystem | watchdog events   | Inbox/*.txt     |
| `gmail_watcher.py`    | Gmail inbox      | IMAP UNSEEN poll  | Inbox/email_*.txt |
| `linkedin_watcher.py` | LinkedIn API     | REST API poll     | Inbox/linkedin_*.txt |

---

## Claude Reasoning Loop (`process_tasks.py`)

Three-step chain-of-thought loop — each step builds on the previous:

1. **Understand** — Claude restates the task to confirm comprehension
2. **Consider** — identifies sensitive actions, missing info, urgency
3. **Plan** — numbered execution plan with specific steps

---

## MCP Server (`mcp_server.py`)

Exposes AI Employee capabilities to Claude Code via MCP protocol.

| Tool                   | Action                                      |
|------------------------|---------------------------------------------|
| `send_email`           | Send email via Gmail SMTP                   |
| `post_to_linkedin`     | Publish post to LinkedIn                    |
| `list_pending_approvals` | Show all tasks awaiting sign-off          |
| `approve_task`         | Move task from Pending_Approval → Approved  |
| `create_task`          | Drop new task into Inbox                    |
| `get_pipeline_status`  | Count files in each stage                   |

**Register with Claude Code** — add to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "ai-employee": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "E:/AI/AI_Employee/AI_Employee"
    }
  }
}
```

---

## Scheduler (`scheduler.py`)

| Job                 | Default Schedule          | Override (.env)                        |
|---------------------|---------------------------|----------------------------------------|
| Gmail check         | Every 60 minutes          | SCHEDULER_GMAIL_INTERVAL_MINUTES       |
| Process tasks       | Every 5 minutes           | SCHEDULER_TASKS_INTERVAL_MINUTES       |
| LinkedIn auto-post  | Every Monday at 09:00     | SCHEDULER_LINKEDIN_DAY / _TIME         |
| Pipeline status log | Every day at 08:00        | —                                      |

---

## Sensitive Action Handling (Human-in-the-Loop)

1. `process_tasks.py` — Step 2 explicitly identifies sensitive actions (email, post, publish)
2. `approval_system.py` — adds a warning banner to the approval request if sensitive keywords detected
3. `action.py` — detects task type and routes to the correct executor:
   - email tasks with a recipient → sends via Gmail SMTP
   - LinkedIn tasks → posts via LinkedIn API
   - all tasks → still require human approval before execution

---

## Running the System

**Terminal 1** — File watcher:
```bash
python file_watcher.py
```

**Terminal 2** — Orchestrator (pipeline brain):
```bash
python orchestrator.py
```

**Terminal 3** — Scheduler (recurring jobs):
```bash
python scheduler.py
```

**Terminal 4** — Gmail watcher (optional, or use scheduler):
```bash
python gmail_watcher.py
```

**Terminal 5** — LinkedIn watcher (optional):
```bash
python linkedin_watcher.py          # watch mode
python linkedin_watcher.py post     # post immediately
```

**MCP Server** (for Claude Code integration):
```bash
python mcp_server.py
```

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your API keys
```

### Environment Variables (`.env`)

| Variable                  | Required for                    |
|---------------------------|---------------------------------|
| ANTHROPIC_API_KEY         | All Claude features             |
| GMAIL_USER                | Gmail watcher, email sending    |
| GMAIL_APP_PASSWORD        | Gmail watcher, email sending    |
| LINKEDIN_ACCESS_TOKEN     | LinkedIn watcher + posting      |
| LINKEDIN_PERSON_URN       | LinkedIn posting                |

---

## Governance

**`Company_Handbook.md`** — rules all agents follow:
- Always be polite
- Ask before sending anything externally (the approval gate enforces this)
- Handle urgent tasks first

Every agent skill references this file. The reasoning loop (Step 2) explicitly checks for policy compliance before generating a plan.
