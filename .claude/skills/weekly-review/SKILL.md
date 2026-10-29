---
name: weekly-review
description: Run a weekly review of this second-brain repo — clean up, triage the inbox, prune stale tasks, flag idle projects, and set the focus for the coming week, saved as Reviews/YYYY-MM-DD.md. Use when the user asks for a review, weekly review, cleanup, or to plan the week.
---

# weekly-review

Goal: keep the system small and pointed at the few things that matter (Pareto). Propose changes, let the user decide, then apply. Keep the conversation brisk — batch questions.

## 1. Gather (commands only, from the repo root)

```
python tools/sb.py lint --fix          # archive ticked tasks, fill missing dates
python tools/sb.py overview
python tools/sb.py log --days 7        # what got done
python tools/sb.py open --stale 30     # old undated tasks
python tools/sb.py open --due 7        # what's coming up
```
Also read `Ideas/inbox.md`, and the `## Focus` section of the most recent `Reviews/*.md` (if any). Don't read `archive.md`, other `Ideas/` files, or task files beyond these outputs unless needed for a specific question.

## 2. Propose, in one message

- **Wins:** a line on what got done vs. last review's focus.
- **Inbox triage:** for each inbox item — move to an `Ideas/` file, make it a project idea, make it a task, or delete.
- **Stale tasks:** for each — keep (maybe with a due date), demote to lowest priority `⏬` (someday), or delete.
- **Projects:** idle ones (flagged in overview) — pause, mark done, or recommit. Missing `priority`/`goal` in a project's `description.md` — suggest values.
- **Focus for next week:** the 3 (at most 5) tasks with the most value per effort, across projects, with a one-line reason each.

- **Plan the week (zoomed out):** ask which project (one or two) the user wants to work on each day, or take their stated plan. Per day, check that the project has the tasks needed to make progress, point out likely missing ones (e.g. a stated goal with no task behind it), and add them. Only project-per-day goes in the review note; specific tasks get picked on the day with `daily-plan`. Use `📅` only for real deadlines; give a task `⏳` here only if it must happen on a specific day.

## 3. Apply what the user approves

- New tasks/ideas and completions: via `sb add-task` / `sb add-idea` / `sb done`.
- Moving/deleting inbox ideas, deleting or re-prioritising tasks, editing `status`/`priority`/`goal`: small direct edits to the files.
- Write `Reviews/YYYY-MM-DD.md` (today's date), terse:
  ```markdown
  # Review YYYY-MM-DD

  ## Done
  - N tasks completed; highlights...

  ## Decisions
  - paused X, deleted N stale tasks, ...

  ## Focus
  1. <project>: <task> — reason
  2. ...

  ## Plan
  - Mon: <project(s)> — <theme/goal for the day>
  - Tue: ...
  ```
- Report what changed in a few lines.
