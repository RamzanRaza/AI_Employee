# Skill: Gmail Watcher

## Description
Monitor Gmail inbox for unread emails and create task files in Inbox/ for the pipeline.

## Trigger
Run `python gmail_watcher.py` in a dedicated terminal, or let the scheduler handle it.

## Steps
1. Connect to Gmail via IMAP (imap.gmail.com)
2. Search for UNSEEN messages
3. For each new email: decode subject + body, write to Inbox/<email_subject>.txt
4. Mark email as read (Seen flag)
5. Sleep for GMAIL_POLL_INTERVAL seconds, then repeat

## Rules
- Follow Company_Handbook
- Never delete emails from Gmail — only mark as read
- Skip files that already exist in Inbox/ (deduplication)
- Sanitize email subjects to safe filenames

## Required Environment Variables
- GMAIL_USER          — your Gmail address
- GMAIL_APP_PASSWORD  — Gmail App Password (not your login password)
                        Generate at: Google Account → Security → App Passwords

## Output
Creates files in Inbox/ with format:
  Source: Gmail
  From: <sender>
  Subject: <subject>

  <email body>
