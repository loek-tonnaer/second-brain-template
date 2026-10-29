---
name: show-open-tasks
description: Show only the still-open (not done) tasks for one or more projects in this second-brain repo, or everything that's due soon. Use when the user asks what's left to do, or wants open/outstanding/pending tasks.
---

# show-open-tasks

Don't read the task files — run from the repo root:

```
python tools/sb.py open <project> [<project>...]   # one or more projects
python tools/sb.py open                            # all non-done projects
python tools/sb.py open --due 7                    # only due/scheduled within 7 days, incl. overdue
```

If the project is unknown/ambiguous, the script lists the slugs — pick the obvious match or ask. Present the output as-is (numbers are what `sb done` accepts). Read-only.
