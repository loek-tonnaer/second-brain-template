---
name: complete-task
description: Mark a task as done in this second-brain repo (adds the done date and moves it to the project's archive.md). Use when the user says they finished, completed, or did a task, or asks to check one off.
---

# complete-task

Don't read the task files — run from the repo root:

```
python tools/sb.py done <project> "<distinctive words from the task>"   # or the task's number from `sb open`
```

- If several tasks match, the script lists them — pick the clearly intended one by number, or ask the user.
- Recurring tasks (`🔁`) get their next occurrence created automatically; if the script says the rule is unsupported, tell the user to tick it in Obsidian.
- Relay the result.
