---
name: show-tasks
description: Show all tasks for a particular project in this second-brain repo, both open and done. Use when the user asks to see, list, or review tasks for a project, including finished ones.
---

# show-tasks

Don't read the task files — run from the repo root:

```
python tools/sb.py show <project>
```

If the project is unknown/ambiguous, the script lists the slugs — pick the obvious match or ask. Present the output. Read-only.
