---
name: add-note
description: Create a note (or append to one) in a project's notes/ folder in this second-brain repo. Use when the user says "make a note", "add a note", or wants to capture longer notes/specs/lists for a project.
---

# add-note

Don't read any files.

1. Pick the project (`-p`); if none is given or implied, ask.
2. Run from the repo root:
   ```
   python tools/sb.py add-note "<title>" -p <project> [-b "<body text>"] [-i "<bullet>"]...
   ```
   - `-i` adds one bullet per item (repeatable); `-b` adds free text (may be multi-line).
   - If a note with that title exists, the content is appended.
   - Keep text terse; fix obvious typos, don't rewrite the user's intent.
3. Relay the script's one-line result.

Short one-line thoughts are ideas → use `add-idea` instead.
