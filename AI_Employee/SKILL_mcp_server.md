# Skill: MCP Server (External Actions)

## Description
An MCP (Model Context Protocol) server that exposes AI Employee tools to Claude Code
and any MCP-compatible client. Enables Claude to directly send emails, post to LinkedIn,
manage the approval pipeline, and create tasks.

## Start the Server
```
python mcp_server.py
```

## Register with Claude Code
Add to .claude/settings.json:
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

## Available Tools

| Tool                    | Description                                      |
|-------------------------|--------------------------------------------------|
| send_email              | Send email via Gmail SMTP                        |
| post_to_linkedin        | Publish a post to LinkedIn                       |
| list_pending_approvals  | Show all tasks awaiting human sign-off           |
| approve_task            | Move a task from Pending_Approval → Approved     |
| create_task             | Drop a new task into Inbox for the pipeline      |
| get_pipeline_status     | Count files in each pipeline stage               |

## Rules
- send_email and post_to_linkedin are sensitive — always confirm intent before calling
- approve_task bypasses the human-review folder; use only when human has confirmed approval
- Follow Company_Handbook policies

## Required Environment Variables
- GMAIL_USER, GMAIL_APP_PASSWORD      (for send_email)
- LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN  (for post_to_linkedin)
