---
name: add-task
description: Append a quick task to the right Projects/<slug>/tasks.md file in this second-brain repo, optionally for a named project. Use when the user says "add a task" or "start a project" alongside a task.
---

# add-task

Don't read any files — the script handles format, dates, and project lookup.

1. If the user says this is a **new project**, use the `add-project` skill (its `--task` option adds the task too) and stop.
2. Run from the repo root, with the project if one was named (omit `-p` → `general`):
   ```
   python tools/sb.py add-task "<terse task text>" -p <project>
   ```
   If the project has subprojects (see `python tools/sb.py overview`) and the task clearly fits one, add `-s <subproject>`; otherwise leave it out.
   Only if the user gave them, add: `--due YYYY-MM-DD`, `--scheduled YYYY-MM-DD`, `--priority highest|high|medium|low|lowest`, `--recur "every week"`. Resolve relative dates ("friday") to absolute ones.
3. If it fails with an unknown/ambiguous project, pick the obvious match from the listed slugs and rerun, or ask the user.
4. Relay the script's one-line result.
