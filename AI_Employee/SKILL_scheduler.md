# Skill: Task Scheduler

## Description
Runs recurring jobs on a cron-like schedule. Automates Gmail checks,
task processing, LinkedIn posting, and pipeline status reporting.

## Start the Scheduler
```
python scheduler.py
```
Run in a dedicated terminal alongside file_watcher.py and orchestrator.py.

## Default Schedule

| Job                  | Frequency                          |
|----------------------|------------------------------------|
| Gmail check          | Every 60 minutes                   |
| Process tasks        | Every 5 minutes                    |
| LinkedIn auto-post   | Every Monday at 09:00              |
| Pipeline status log  | Every day at 08:00                 |

## Override via .env

```
SCHEDULER_GMAIL_INTERVAL_MINUTES=30
SCHEDULER_TASKS_INTERVAL_MINUTES=10
SCHEDULER_LINKEDIN_DAY=wednesday
SCHEDULER_LINKEDIN_TIME=10:00
```

## Logs
All job output is written to Logs/scheduler.log with timestamps.

## Rules
- Follow Company_Handbook: LinkedIn posts only run on scheduled days
- Do not reduce TASKS interval below 2 minutes (API rate limits)
- Scheduler does not replace orchestrator.py — both should run simultaneously
