---
name: add-idea
description: Append a quick idea to the right Ideas/ file, or to a project's ideas.md, in this second-brain repo. Use when the user says "add an idea" or gives you a piece of text to capture as an idea.
---

# add-idea

Don't read any files.

1. Pick the destination:
   - Tied to a specific project → `-p <project>` (goes to `Projects/<slug>/ideas.md`).
   - Otherwise `--to <topic>`: an existing `Ideas/<topic>.md` that clearly fits (list them with `Glob Ideas/*.md`; the `overview` output also names them), else `inbox` (anything else, or unsure). Create a new topic only when the user asks for one.
2. Run from the repo root:
   ```
   python tools/sb.py add-idea "<terse idea text>" --to <file>     # or: -p <project>
   ```
   Keep the text terse — trim filler, don't rewrite the user's intent.
3. Relay the script's one-line result.
