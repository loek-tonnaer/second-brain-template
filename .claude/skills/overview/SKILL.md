---
name: overview
description: Give a compact overview of all projects in this second-brain repo (status, priority, goal, open/overdue/due-soon counts, idle projects, top next task, idea counts), as the starting point for "what should I work on next", planning, or brainstorming. Use when the user asks for an overview, status, or advice on what to do next.
---

# overview

1. Run from the repo root: `python tools/sb.py overview` (add `--all` to include done projects).
2. For a plain overview, present it and stop.
3. For advice ("what next?", prioritising), load more only as needed, cheapest first:
   - The `## Focus` section of the most recent `Reviews/*.md`, if any — the user's own chosen priorities.
   - `python tools/sb.py open [<project>...]` for the open tasks of relevant projects; `--due 7` for deadlines.
   - `Projects/<slug>/description.md` (and `roadmap.md`/`ideas.md` if they exist) for the projects in question.
   - `Ideas/*.md` only when brainstorming what to start.
   - Never `archive.md` unless the user asks about history; use `sb log --days N` for recent progress.
   Apply the Pareto principle: weigh project `priority`/`goal`, recommend the few tasks with the most value per effort, and say which to drop, defer, or pause.
