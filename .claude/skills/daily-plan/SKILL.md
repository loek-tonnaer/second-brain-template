---
name: daily-plan
description: Plan the day in this second-brain repo — pick the specific tasks to work on today from the project(s) planned for today, fill gaps, and schedule them so they show up in Today.md. Use when the user says "plan my day", "daily plan", "what am I doing today", or starts a work day.
---

# daily-plan

Goal: a short, realistic list of tasks for today (one or two product projects), scheduled with `⏳ today` so `Today.md` shows exactly what to do. Keep it brisk; propose, let the user decide, then apply.

## 1. Gather (from the repo root)

```
python tools/sb.py open --due 0        # due/scheduled today and overdue
python tools/sb.py open <proj>...      # all open tasks of today's project(s)
```
Today's project(s): the user's answer, else the matching day in the `## Plan` of the most recent `Reviews/*.md`. If neither is known, ask. Don't read `archive.md` or other files unless needed.

## 2. Propose, in one message

- **Already today:** tasks due or scheduled today, and overdue ones that belong to today's project(s) — keep, or push (clear/reschedule the date).
- **Candidates:** the most valuable open tasks of today's project(s), by priority, then age, with a one-line reason; aim for what fits a day (about 3–6 tasks; ask about available time if unclear).
- **Missing:** tasks the day's goal needs that don't exist yet — propose them as new tasks.
- **Overdue elsewhere:** one line on overdue tasks from other projects, so none are lost: do today, reschedule, or drop the date.

## 3. Apply what the user approves

- Schedule: `python tools/sb.py schedule <proj> <YYYY-MM-DD today> <number|text>`.
- New tasks: `python tools/sb.py add-task ... --scheduled <today>`.
- Push/clear: `sb schedule <proj> <date|none> ...` (or `sb due` for 📅 deadlines).
- Report in a few lines what is on today's list. Tasks ticked in Obsidian stay on `Today.md` until tomorrow; no extra step needed.
