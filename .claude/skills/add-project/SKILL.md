---
name: add-project
description: Create a new project folder in this second-brain repo (Projects/<slug>/ with description.md and tasks.md). Use when the user says "start a project," "add a project," or "new project."
---

# add-project

1. Pick a `type`: the one the user named, or an existing one that obviously fits — check with `Grep` for `^type:` in `Projects/*/description.md` (don't read the files). Otherwise ask, or use `general` for a one-off.
2. Run from the repo root (the slug is derived from the name):
   ```
   python tools/sb.py add-project "<name or slug>" --type <type> --description "<one paragraph>" [--task "<first task>"]
   ```
3. If it reports the project already exists, tell the user instead of retrying.
4. Relay the result.
