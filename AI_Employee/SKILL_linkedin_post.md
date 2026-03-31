# Skill: LinkedIn Auto-Post

## Description
Generate a professional LinkedIn business post via Claude and publish it automatically
to attract sales leads. Can also watch for LinkedIn notifications.

## Trigger
- Automatic: scheduler runs every Monday at 09:00
- Manual:    `python linkedin_watcher.py post`
- Custom:    `python linkedin_watcher.py post "topic here"`
- Watch:     `python linkedin_watcher.py` (polls notifications)

## Steps
1. Receive topic (or use default B2B AI services prompt)
2. Call Claude to generate a compelling post (under 280 words, 2-3 emojis, CTA)
3. POST to LinkedIn API v2 /ugcPosts endpoint
4. Save copy to Done/linkedin_post_<timestamp>.md
5. Log result

## Rules
- Follow Company_Handbook: ask before sending (handled by scheduler — Monday only)
- Post should be professional, value-driven, no spam
- Never post more than once per scheduled run

## Required Environment Variables
- LINKEDIN_ACCESS_TOKEN  — OAuth2 bearer token (expires; must refresh periodically)
- LINKEDIN_PERSON_URN    — format: urn:li:person:XXXXXXXXX
                           Find via: GET https://api.linkedin.com/v2/me

## Output
- Posts to LinkedIn (public)
- Saves content to Done/linkedin_post_YYYYMMDD_HHMMSS.md
