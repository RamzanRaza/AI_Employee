# AI Employee — Architecture Overview

An event-driven AI workflow system built on an Obsidian vault, implementing a human-in-the-loop pipeline where tasks flow through staged folders from inbox to completion.

---

## Project Goals

- Obsidian vault with `Dashboard.md` and `Company_Handbook.md` as governance layer
- File system monitoring via a Watcher script
- Claude Code reading from and writing to the vault
- Folder-based pipeline: `/Inbox` → `/Needs_Action` → `/Done`
- All AI functionality implemented as Agent Skills

---

## Folder Structure

```
AI_Employee/
├── Inbox/                    # Drop new tasks here
├── Needs_Action/             # Validated tasks awaiting planning
├── Plans/                    # AI-generated plans for each task
├── Pending_Approval/         # Plans awaiting human sign-off
├── Approved/                 # Human-approved plans ready to execute
├── Done/                     # Completed tasks (archive)
├── Logs/                     # Execution audit trail (log.txt)
│
├── file_watcher.py           # Stage 1 — monitors Inbox
├── orchestrator.py           # Central event hub
├── process_tasks.py          # Stage 2 — generates plans
├── approval_system.py        # Stage 3 — creates approval requests
├── action.py                 # Stage 4 — executes approved tasks
│
├── SKILL_process_tasks.md    # Claude Code skill definition
├── Company_Handbook.md       # Policy rules enforced by all agents
└── Dashboard.md              # Task status dashboard
```

---

## Architecture

### Pipeline Flow

```
Inbox/ ──► Needs_Action/ ──► Plans/ ──► Pending_Approval/
                                              │
                                        [Human Review]
                                              │
                                          Approved/ ──► Done/
                                                         │
                                                      Logs/log.txt
```

### Components

#### `file_watcher.py` — Stage 1: Intake
Monitors `Inbox/` using the `watchdog` library. When a file with content appears, it copies it to `Needs_Action/`. Skips empty files and waits 0.5s for writes to stabilize before processing.

#### `orchestrator.py` — Central Coordinator
Event-driven hub that watches three folders simultaneously and spawns the appropriate subprocess when a file event fires:

| Folder watched   | Script triggered      |
|------------------|-----------------------|
| `Needs_Action/`  | `process_tasks.py`    |
| `Plans/`         | `approval_system.py`  |
| `Approved/`      | `action.py`           |

#### `process_tasks.py` — Stage 2: Planning
Reads each task file and writes a structured `PLAN_<filename>.md` into `Plans/`, containing task understanding, steps (Analyze → Decide → Prepare → Request Approval), and a timestamp.

#### `approval_system.py` — Stage 3: Human Gate
Reads each plan and writes an `APPROVAL_<plan>.md` into `Pending_Approval/`. Instructions direct the human reviewer to move the file to `Approved/` to proceed — enforcing the Company Handbook rule: *"Ask before sending anything."*

#### `action.py` — Stage 4: Execution
Iterates `Approved/`, executes each task, appends a timestamped entry to `Logs/log.txt`, and moves the file to `Done/`.

---

## Governance

### `Company_Handbook.md`
Global policy rules all agents must follow:
- Always be polite
- Ask before sending anything (the approval gate enforces this)
- Handle urgent tasks first

### `SKILL_process_tasks.md`
Claude Code skill definition that documents the "Process Tasks" workflow. References `Company_Handbook.md` for compliance and defines the step-by-step rules agents follow when processing a task.

---

## Workflow Example

1. User drops `linkedin_post.txt` into `Inbox/`
2. `file_watcher.py` detects the file and copies it to `Needs_Action/`
3. `orchestrator.py` triggers `process_tasks.py` → creates `Plans/PLAN_linkedin_post.md`
4. `orchestrator.py` triggers `approval_system.py` → creates `Pending_Approval/APPROVAL_PLAN_linkedin_post.md`
5. Human reviews and moves the file to `Approved/`
6. `orchestrator.py` triggers `action.py` → logs execution, moves file to `Done/`

---

## Key Design Decisions

- **File-based state** — each folder represents a pipeline stage; easy to inspect and debug
- **Human-in-the-loop** — no task executes without explicit human approval
- **Event-driven** — `watchdog` observers eliminate polling; each stage reacts to file creation
- **Process isolation** — each stage runs as a separate Python subprocess via `orchestrator.py`
- **Audit trail** — every execution is logged with a timestamp in `Logs/log.txt`

---

## Dependencies

```
watchdog    # File system event monitoring
pathlib     # Cross-platform file handling (stdlib)
shutil      # File copy/move operations (stdlib)
datetime    # Timestamps (stdlib)
subprocess  # Spawning stage scripts (stdlib)
```

Install:
```bash
pip install watchdog
```

## Running

Start the watcher and orchestrator in separate terminals:

```bash
python file_watcher.py
python orchestrator.py
```

Then drop task files into `Inbox/` to begin the pipeline.
