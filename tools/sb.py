#!/usr/bin/env python3
"""sb - second-brain CLI: the shared interface for the user, Obsidian and AI agents.

Run from anywhere: python tools/sb.py <command> ...   (or `sb <command>` via sb.cmd on Windows)
Every command prints compact output so agents can use it without reading whole files.
Standard library only.
"""
import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "Projects"
IDEAS = ROOT / "Ideas"
STATUSES = ["active", "paused", "done"]
TODAY = dt.date.today()

TASK_RE = re.compile(r"^- \[(.)\] (.*)$")
DATE = r"\s*(\d{4}-\d{2}-\d{2})"
CREATED, DUE, SCHEDULED, DONE, CANCELLED = "➕", "📅", "⏳", "✅", "❌"
PRIORITIES = {"highest": "🔺", "high": "⏫", "medium": "🔼", "low": "🔽", "lowest": "⏬"}
PRIO_RANK = {"🔺": 0, "⏫": 1, "🔼": 2, "🔽": 4, "⏬": 5}  # no priority ranks 3, like Tasks
RECUR_RE = re.compile(r"🔁\s*every\s+(\d+\s+)?(day|week|month|year)s?\b", re.I)
IDEA_DATE_RE = re.compile(r"^- \(\d{4}-\d{2}-\d{2}\) ")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def rel(path):
    return path.relative_to(ROOT).as_posix()


# ---------- files ----------

def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def write_lines(path, lines):
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def append_line(path, line, header):
    lines = read_lines(path) or [header]
    while lines and not lines[-1].strip():
        lines.pop()
    if lines[-1].startswith("#"):
        lines.append("")
    write_lines(path, lines + [line])


def frontmatter(path):
    lines = read_lines(path)
    meta = {}
    if lines[:1] == ["---"]:
        for line in lines[1:]:
            if line == "---":
                break
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("\"'")
    return meta


# ---------- tasks ----------

class Task:
    def __init__(self, status, text):
        self.status, self.text, self.children = status, text, []
        self.sub = ""  # subproject: the `## heading` the task sits under ("" = main project)

    @property
    def open(self):
        return self.status not in "xX-"

    def date(self, sign):
        m = re.search(re.escape(sign) + DATE, self.text)
        return dt.date.fromisoformat(m.group(1)) if m else None

    def rank(self, index):
        prio = next((r for s, r in PRIO_RANK.items() if s in self.text), 3)
        return (prio, self.date(DUE) or dt.date.max, index)

    def lines(self):
        return [f"- [{self.status}] {self.text}"] + self.children


def parse(lines):
    """Lines -> list of Task or str. Indented lines after a task belong to it (subtasks, notes)."""
    items, sub = [], ""
    for line in lines:
        m = TASK_RE.match(line)
        if line.startswith("## "):
            sub = line[3:].strip()
        if m:
            items.append(Task(m.group(1), m.group(2)))
            items[-1].sub = sub
        elif line[:1] in (" ", "\t") and items and isinstance(items[-1], Task):
            items[-1].children.append(line)
        else:
            items.append(line)
    return items


def render(items):
    out = []
    for it in items:
        out += it.lines() if isinstance(it, Task) else [it]
    return tidy(out)


def tidy(lines):
    """Exactly one blank line around each heading; other blank lines are left alone."""
    out = []
    for i, line in enumerate(lines):
        head = line.startswith("#")
        after_head = out and (out[-1].startswith("#") or (not out[-1] and len(out) > 1 and out[-2].startswith("#")))
        if not line.strip() and (after_head or (i + 1 < len(lines) and lines[i + 1].startswith("#"))):
            continue
        if head and out:
            out.append("")
        out.append(line)
        if head:
            out.append("")
    return out


def insert_task(items, task, sub):
    """Put task at the end of its subproject's section (created at the end if new; "" = before the first ## heading)."""
    task.sub = sub
    heads = [i for i, it in enumerate(items) if isinstance(it, str) and it.startswith("## ")]
    if not sub:
        end = heads[0] if heads else len(items)
    else:
        start = next((i for i in heads if items[i][3:].strip() == sub), None)
        if start is None:
            items.append(f"## {sub}")
            start = len(items) - 1
            heads.append(start)
        end = next((i for i in heads if i > start), len(items))
    while end > 0 and isinstance(items[end - 1], str) and not items[end - 1].strip():
        end -= 1
    items.insert(end, task)


def subprojects(slug):
    """Subproject names of a project, in file order (tasks.md first, then archive-only ones)."""
    names = []
    for f in ("tasks.md", "archive.md"):
        names += [l[3:].strip() for l in read_lines(pdir(slug) / f) if l.startswith("## ")]
    return list(dict.fromkeys(names))


def resolve_sub(slug, name):
    """Existing subproject by case-insensitive exact name or unique substring; else the name as given (new)."""
    if name.strip().lower() in ("", "none", "main"):
        return ""
    subs = subprojects(slug)
    exact = [x for x in subs if x.lower() == name.strip().lower()]
    part = [x for x in subs if name.strip().lower() in x.lower()]
    return (exact or (part if len(part) == 1 else []) or [name.strip()])[0]


def tasks_of(items):
    return [it for it in items if isinstance(it, Task)]


# ---------- projects ----------

def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def all_projects():
    return sorted(p.name for p in PROJECTS.iterdir() if (p / "tasks.md").exists())


def resolve(name):
    slugs, s = all_projects(), slugify(name)
    if s in slugs:
        return s
    hits = [p for p in slugs if s in p]
    if len(hits) == 1:
        return hits[0]
    die(f"Unknown or ambiguous project '{name}'. Projects: {', '.join(slugs)}")


def pdir(slug):
    return PROJECTS / slug


def status_of(slug):
    return frontmatter(pdir(slug) / "description.md").get("status", "?")


def listed_projects(names, include_done=False):
    if names:
        return [resolve(n) for n in names]
    order = {s: i for i, s in enumerate(STATUSES)}
    slugs = [s for s in all_projects() if include_done or status_of(s) != "done"]

    def key(s):
        meta = frontmatter(pdir(s) / "description.md")
        prio = meta.get("priority", "")
        return (order.get(meta.get("status"), 9), int(prio) if prio.isdigit() else 9, s)
    return sorted(slugs, key=key)


def last_activity(slug):
    """Latest ➕/✅ date in the project's tasks and archive, or its start date."""
    text = "\n".join(line for f in ("tasks.md", "archive.md") for line in read_lines(pdir(slug) / f))
    found = re.findall(f"[{CREATED}{DONE}]" + DATE, text)
    started = frontmatter(pdir(slug) / "description.md").get("started", "")
    found += [started] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", started) else []
    return max(map(dt.date.fromisoformat, found), default=None)


def open_tasks(slug):
    return [t for t in tasks_of(parse(read_lines(pdir(slug) / "tasks.md"))) if t.open]


def archive(slug):
    """Move closed tasks from tasks.md to archive.md, and reopened ones back. Returns (moved, reopened)."""
    tpath, apath = pdir(slug) / "tasks.md", pdir(slug) / "archive.md"
    titems, aitems = parse(read_lines(tpath)), parse(read_lines(apath))
    closed = [t for t in tasks_of(titems) if not t.open]
    reopened = [t for t in tasks_of(aitems) if t.open]
    if not closed and not reopened:
        return 0, 0
    for t in closed:
        if t.status in "xX" and DONE not in t.text:
            t.text += f" {DONE} {TODAY}"  # ticked without the Tasks plugin: use archive date
    titems = [it for it in titems if it not in closed]
    aitems = [it for it in aitems if it not in reopened]
    if not aitems or aitems[0] != f"# Archive: {slug}":
        aitems = [f"# Archive: {slug}", ""] + aitems
    for t in reopened:
        insert_task(titems, t, t.sub)
    for t in closed:
        insert_task(aitems, t, t.sub)
    write_lines(tpath, render(titems))
    write_lines(apath, render(aitems))
    return len(closed), len(reopened)


def next_occurrence(task):
    """Basic 🔁 support: 'every [N] day|week|month|year', shifting 📅/⏳ dates. None if unsupported."""
    m = RECUR_RE.search(task.text)
    if not m or not (task.date(DUE) or task.date(SCHEDULED)):
        return None
    n, unit = int(m.group(1) or 1), m.group(2).lower()

    def shift(d):
        if unit in ("day", "week"):
            return d + dt.timedelta(days=n * (7 if unit == "week" else 1))
        months = d.month - 1 + n * (12 if unit == "year" else 1)
        y, mo = d.year + months // 12, months % 12 + 1
        last = (dt.date(y + mo // 12, mo % 12 + 1, 1) - dt.timedelta(days=1)).day
        return dt.date(y, mo, min(d.day, last))

    text = task.text
    for sign in (DUE, SCHEDULED):
        d = task.date(sign)
        if d:
            text = re.sub(re.escape(sign) + DATE, f"{sign} {shift(d)}", text)
    text = re.sub(re.escape(CREATED) + DATE, f"{CREATED} {TODAY}", text)
    return Task(" ", text)


# ---------- commands ----------

def cmd_add_task(a):
    slug = resolve(a.project or "general")
    text = " ".join(a.text).strip()
    parts = [text, f"{CREATED} {TODAY}"]
    if a.due:
        parts.append(f"{DUE} {dt.date.fromisoformat(a.due)}")
    if a.scheduled:
        parts.append(f"{SCHEDULED} {dt.date.fromisoformat(a.scheduled)}")
    if a.priority:
        parts.append(PRIORITIES[a.priority])
    if a.recur:
        parts.append(f"🔁 {a.recur}")
    archive(slug)
    sub = resolve_sub(slug, a.sub or "")
    is_new = bool(sub) and sub not in subprojects(slug)
    path = pdir(slug) / "tasks.md"
    items = parse(read_lines(path)) or [f"# Tasks: {slug}"]
    insert_task(items, Task(" ", " ".join(parts)), sub)
    write_lines(path, render(items))
    print(f"Added to {rel(path)}" + (f" [{sub}]" if sub else "") + (" (new subproject)" if is_new else ""))


def idea_topics():
    # Ideas/<topic>.md files, inbox first; a new topic is created by add-idea --to
    topics = sorted(p.stem for p in IDEAS.glob("*.md"))
    return ["inbox"] + [t for t in topics if t != "inbox"]


def cmd_add_idea(a):
    text = " ".join(a.text).strip()
    if a.project:
        slug = resolve(a.project)
        path, header = pdir(slug) / "ideas.md", f"# Ideas: {slug}"
    else:
        topic = slugify(a.to)
        path, header = IDEAS / f"{topic}.md", f"# Ideas: {topic}"
        if topic not in idea_topics():
            print(f"New idea topic: {topic}")
    append_line(path, f"- ({TODAY}) {text}", header)
    print(f"Added to {rel(path)}")


def cmd_add_project(a):
    slug = slugify(a.slug)
    d = pdir(slug)
    if d.exists():
        die(f"Project '{slug}' already exists.")
    d.mkdir(parents=True)
    write_lines(d / "description.md", [
        "---", "status: active", f"type: {a.type}", f"priority: {a.project_priority or ''}".rstrip(),
        f"goal: {a.goal or ''}".rstrip(), f"started: {TODAY}", "---", "",
        a.description.strip(), "", "Links: [tasks](tasks.md)"])
    write_lines(d / "tasks.md", [f"# Tasks: {slug}"])
    print(f"Created {rel(d)}/ (description.md, tasks.md)")
    if a.task:
        a.project, a.text = slug, [a.task]
        a.due = a.scheduled = a.priority = a.recur = None
        cmd_add_task(a)


def cmd_add_note(a):
    slug = resolve(a.project)
    path = pdir(slug) / "notes" / f"{slugify(a.title)}.md"
    body = (a.body.strip().splitlines() if a.body else []) + [f"- {i}" for i in a.item or []]
    exists = path.exists()
    if exists and not body:
        die(f"{rel(path)} already exists; pass --body/--item to append.")
    path.parent.mkdir(exist_ok=True)
    lines = read_lines(path) or [f"# {a.title.strip()}"]
    if body:
        lines += [""] + body if lines[-1].startswith("#") or not body[0].startswith("- ") else body
    write_lines(path, lines)
    print(f"{'Appended to' if exists else 'Created'} {rel(path)}")


def print_tasks(tasks, numbered=True):
    """tasks: (number, Task) pairs or plain Tasks; a `### name` line precedes each subproject group."""
    tasks = [p if isinstance(p, tuple) else (i, p) for i, p in enumerate(tasks, 1)]
    grouped = any(t.sub for _, t in tasks)
    last = None
    for i, t in tasks:
        if grouped and t.sub != last:
            print(f"  ### {t.sub or 'main'}")
        last = t.sub
        print(f"  {i}. {t.text}" if numbered else f"  - {t.text}")


def cmd_open(a):
    horizon = TODAY + dt.timedelta(days=a.due) if a.due is not None else None
    cutoff = TODAY - dt.timedelta(days=a.stale) if a.stale is not None else None
    shown = 0
    for slug in listed_projects(a.projects):
        tasks = list(enumerate(open_tasks(slug), 1))
        if horizon:
            tasks = [(i, t) for i, t in tasks
                     if min(filter(None, [t.date(DUE), t.date(SCHEDULED)]), default=dt.date.max) <= horizon]
        if cutoff:
            tasks = [(i, t) for i, t in tasks if not t.date(DUE) and (t.date(CREATED) or TODAY) <= cutoff]
        if not tasks and not a.projects:
            continue
        status = status_of(slug)
        print(f"## {slug}" + (f" ({status})" if status != "active" else "") + f" - {len(tasks)} open")
        print_tasks(tasks)
        shown += len(tasks)
    if not shown and not a.projects:
        print("No matching open tasks.")


def cmd_log(a):
    since = TODAY - dt.timedelta(days=a.days)
    done = []
    for slug in listed_projects(a.projects, include_done=True):
        for f in ("tasks.md", "archive.md"):
            for t in tasks_of(parse(read_lines(pdir(slug) / f))):
                d = t.date(DONE)
                if not t.open and d and d >= since:
                    done.append((d, slug, t.text))
    for d, slug, text in sorted(done):
        print(f"{d} {slug}: {re.sub(re.escape(DONE) + DATE, '', text).strip()}")
    if not done:
        print(f"Nothing completed in the last {a.days} days.")


def cmd_show(a):
    slug = resolve(a.project)
    items = tasks_of(parse(read_lines(pdir(slug) / "tasks.md")))
    done = [t for t in items if not t.open] + tasks_of(parse(read_lines(pdir(slug) / "archive.md")))
    opened = [t for t in items if t.open]
    print(f"## {slug} - open ({len(opened)})")
    print_tasks(opened) if opened else print("  (none)")
    print(f"## {slug} - done ({len(done)})")
    print_tasks(done, numbered=False) if done else print("  (none)")


def cmd_done(a):
    slug = resolve(a.project)
    path = pdir(slug) / "tasks.md"
    items = parse(read_lines(path))
    opened = [t for t in tasks_of(items) if t.open]
    query = " ".join(a.match).strip()
    if query.isdigit():
        hits = [opened[int(query) - 1]] if 0 < int(query) <= len(opened) else []
    else:
        hits = [t for t in opened if query.lower() in t.text.lower()]
    if len(hits) != 1:
        print(f"{'No' if not hits else 'Multiple'} open tasks in {slug} match '{query}':", file=sys.stderr)
        for t in hits or opened:
            print(f"  {opened.index(t) + 1}. {t.text}", file=sys.stderr)
        sys.exit(1)
    task = hits[0]
    if "🔁" in task.text:
        nxt = next_occurrence(task)
        if not nxt:
            die("Recurring rule not supported here (only 'every [N] day|week|month|year' with a 📅/⏳ date). "
                "Tick it in Obsidian instead.")
        items.insert(items.index(task), nxt)
        print(f"Next occurrence: {nxt.text}")
    task.status = "x"
    task.text += f" {DONE} {TODAY}"
    write_lines(path, render(items))
    archive(slug)
    print(f"Done: {task.text}")


def pick(slug, items, match):
    """The one open task matching a number (from `open`) or unique text; exits listing candidates otherwise."""
    opened = [t for t in tasks_of(items) if t.open]
    query = " ".join(match).strip()
    if query.isdigit():
        hits = [opened[int(query) - 1]] if 0 < int(query) <= len(opened) else []
    else:
        hits = [t for t in opened if query.lower() in t.text.lower()]
    if len(hits) != 1:
        print(f"{'No' if not hits else 'Multiple'} open tasks in {slug} match '{query}':", file=sys.stderr)
        for t in hits or opened:
            print(f"  {opened.index(t) + 1}. {t.text}", file=sys.stderr)
        sys.exit(1)
    return hits[0]


def cmd_move(a):
    slug = resolve(a.project)
    path = pdir(slug) / "tasks.md"
    items = parse(read_lines(path))
    task = pick(slug, items, a.match)
    dest = resolve(a.to) if a.to else slug
    sub = resolve_sub(dest, a.sub)
    items.remove(task)
    if dest == slug:
        insert_task(items, task, sub)
    write_lines(path, render(items))
    if dest != slug:
        dpath = pdir(dest) / "tasks.md"
        ditems = parse(read_lines(dpath)) or [f"# Tasks: {dest}"]
        insert_task(ditems, task, sub)
        write_lines(dpath, render(ditems))
    where = (f"{dest} " if dest != slug else "") + (sub or "main project")
    print(f"Moved to {where}: {task.text}")


def cmd_cancel(a):
    slug = resolve(a.project)
    path = pdir(slug) / "tasks.md"
    items = parse(read_lines(path))
    task = pick(slug, items, a.match)
    task.status = "-"
    task.text += f" {CANCELLED} {TODAY}"
    write_lines(path, render(items))
    archive(slug)
    print(f"Cancelled: {task.text}")


def cmd_edit(a):
    slug = resolve(a.project)
    path = pdir(slug) / "tasks.md"
    items = parse(read_lines(path))
    opened = [t for t in tasks_of(items) if t.open]
    query = " ".join(a.match).strip()
    if query.isdigit():
        hits = [opened[int(query) - 1]] if 0 < int(query) <= len(opened) else []
    else:
        hits = [t for t in opened if query.lower() in t.text.lower()]
    if len(hits) != 1:
        print(f"{'No' if not hits else 'Multiple'} open tasks in {slug} match '{query}':", file=sys.stderr)
        for t in hits or opened:
            print(f"  {opened.index(t) + 1}. {t.text}", file=sys.stderr)
        sys.exit(1)
    task = hits[0]
    new = a.text.strip()
    if not new:
        die("New text is empty.")
    # keep the signifiers (dates, priority, recurrence), replace only the description before them
    m = re.search(r"[➕📅⏳✅🔁🔺⏫🔼🔽⏬]", task.text)
    tail = task.text[m.start():] if m else ""
    task.text = f"{new} {tail}".strip()
    write_lines(path, render(items))
    print(f"Edited in {slug}: {task.text}")


def cmd_due(a):
    field = getattr(a, "field", DUE)
    name = "Scheduled" if field == SCHEDULED else "Due"
    slug = resolve(a.project)
    path = pdir(slug) / "tasks.md"
    items = parse(read_lines(path))
    opened = [t for t in tasks_of(items) if t.open]
    if a.date.lower() == "none":
        new = None
    else:
        try:
            new = dt.date.fromisoformat(a.date)
        except ValueError:
            die(f"Invalid date '{a.date}' (use YYYY-MM-DD or 'none').")
    query = " ".join(a.match).strip()
    if a.before:
        if query:
            die("Give either a task or --before, not both.")
        cutoff = dt.date.fromisoformat(a.before)
        hits = [t for t in opened if t.date(field) and t.date(field) < cutoff]
        if not hits:
            die(f"No open tasks in {slug} {name.lower()} before {cutoff}.")
    else:
        if not query:
            die("Give a task number/text or --before DATE.")
        hits = [t for t in opened if query.lower() in t.text.lower()] if not query.isdigit() else             ([opened[int(query) - 1]] if 0 < int(query) <= len(opened) else [])
        if len(hits) != 1:
            print(f"{'No' if not hits else 'Multiple'} open tasks in {slug} match '{query}':", file=sys.stderr)
            for t in hits or opened:
                print(f"  {opened.index(t) + 1}. {t.text}", file=sys.stderr)
            sys.exit(1)
    for t in hits:
        t.text = re.sub(re.escape(field) + DATE, "", t.text).strip()
        if new:
            t.text += f" {field} {new}"
    write_lines(path, render(items))
    print(f"{name} {new or 'removed'} for {len(hits)} task(s) in {slug}:")
    print_tasks(hits, numbered=False)


def cmd_add_sub(a):
    slug = resolve(a.project)
    name = " ".join(a.name).strip()
    if name in subprojects(slug):
        die(f"Subproject '{name}' already exists in {slug}.")
    path = pdir(slug) / "tasks.md"
    write_lines(path, render(parse(read_lines(path)) + [f"## {name}"]))
    print(f"Added subproject '{name}' to {slug}")


def cmd_archive(a):
    total = 0
    for slug in listed_projects(a.projects, include_done=True):
        moved, reopened = archive(slug)
        if moved or reopened:
            print(f"{slug}: archived {moved}" + (f", reopened {reopened}" if reopened else ""))
        total += moved + reopened
    if not total:
        print("Nothing to archive.")


def blame_dates(path):
    """1-based line number -> date the line was last changed (today if uncommitted)."""
    try:
        out = subprocess.run(["git", "blame", "--porcelain", "--", rel(path)], cwd=ROOT, check=True,
                             capture_output=True, text=True, encoding="utf-8").stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    dates, times, cur = {}, {}, None
    for line in out.splitlines():
        m = re.match(r"^([0-9a-f]{40}) \d+ (\d+)", line)
        if m:
            cur = (m.group(1), int(m.group(2)))
        elif line.startswith("author-time "):
            times[cur[0]] = int(line.split()[1])
        elif line.startswith("\t") and cur:
            t = times.get(cur[0])
            dates[cur[1]] = TODAY if set(cur[0]) == {"0"} or t is None else dt.date.fromtimestamp(t)
    return dates


def cmd_lint(a):
    issues = []
    for slug in all_projects():
        d = pdir(slug)
        meta = frontmatter(d / "description.md")
        if not (d / "description.md").exists():
            issues.append(f"{slug}: missing description.md")
        elif meta.get("status") not in STATUSES or not meta.get("type") or not meta.get("started"):
            issues.append(f"{slug}: description.md frontmatter needs status ({'|'.join(STATUSES)}), type, started")
        if meta.get("priority", "") not in ("", "1", "2", "3"):
            issues.append(f"{slug}: priority must be 1, 2, 3 or empty")
        titems = tasks_of(parse(read_lines(d / "tasks.md")))
        closed = sum(not t.open for t in titems)
        reopened = sum(t.open for t in tasks_of(parse(read_lines(d / "archive.md"))))
        if closed or reopened:
            if a.fix:
                archive(slug)
            issues.append(f"{slug}: {closed} done task(s) in tasks.md, {reopened} open in archive.md"
                          + (" -> fixed" if a.fix else ""))
        path = d / "tasks.md"
        lines = read_lines(path)
        missing = [i for i, line in enumerate(lines) if TASK_RE.match(line) and CREATED not in line]
        if missing:
            if a.fix:
                dates = blame_dates(path)
                for i in missing:
                    lines[i] += f" {CREATED} {dates.get(i + 1, TODAY)}"
                write_lines(path, lines)
            issues.append(f"{slug}: {len(missing)} task(s) without {CREATED} date"
                          + (" -> fixed (from git history)" if a.fix else ""))
    for path in sorted(IDEAS.glob("*.md")) + sorted(PROJECTS.glob("*/ideas.md")):
        bad = [l for l in read_lines(path) if l.startswith("- ") and not IDEA_DATE_RE.match(l)]
        if bad:
            issues.append(f"{rel(path)}: {len(bad)} idea(s) without (YYYY-MM-DD) date")
    print("\n".join(issues) if issues else "All good.")
    sys.exit(1 if issues and not a.fix else 0)


def cmd_overview(a):
    horizon = TODAY + dt.timedelta(days=7)
    for slug in listed_projects([], include_done=a.all):
        meta = frontmatter(pdir(slug) / "description.md")
        tasks = open_tasks(slug)
        dues = [t.date(DUE) for t in tasks if t.date(DUE)]
        overdue = sum(d < TODAY for d in dues)
        soon = sum(TODAY <= d <= horizon for d in dues)
        ideas = sum(IDEA_DATE_RE.match(l) is not None for l in read_lines(pdir(slug) / "ideas.md"))
        stats = [f"{len(tasks)} open"] + [f"{overdue} overdue"] * bool(overdue) \
            + [f"{soon} due ≤7d"] * bool(soon) + [f"{ideas} ideas"] * bool(ideas)
        last = last_activity(slug)
        if slug != "general" and last and meta.get("status") == "active" and (TODAY - last).days > a.idle:
            stats.append(f"idle {(TODAY - last).days}d")
        tags = [meta.get("status", "?"), meta.get("type", "?")] + [f"p{meta['priority']}"] * bool(meta.get("priority"))
        print(f"{slug} [{', '.join(tags)}] {', '.join(stats)}")
        if meta.get("goal"):
            print(f"  goal: {meta['goal']}")
        subs = {n: sum(t.sub == n for t in tasks) for n in subprojects(slug)}
        if subs:
            print("  subprojects: " + ", ".join(f"{n} {c}" for n, c in subs.items()))
        if tasks:
            top = min(enumerate(tasks), key=lambda p: p[1].rank(p[0]))[1]
            print(f"  next: {top.text[:110]}")
    counts = [f"{f} {sum(IDEA_DATE_RE.match(l) is not None for l in read_lines(IDEAS / (f + '.md')))}"
              for f in idea_topics()]
    print("Ideas: " + ", ".join(counts))


def week_block(date, today):
    # Tasks queries can't use relative weekdays without JavaScript, so dates are written out
    lines = ["```tasks"]
    if date != today:
        lines.append("not done")
    lines += [f"happens on {date}", "path includes Projects/"]
    if date == today:
        lines.append("sort by done")
    lines += ["sort by priority", "group by folder", "group by heading", "hide backlink", "```", ""]
    return lines


def week_page(title, monday, today, older=False):
    out = ["---", "cssclasses: section-headers", "---", f"# {title}", "",
           "Obsidian-only view (Tasks plugin), by due or scheduled date. Weeks run Monday to Sunday. "
           "Generated by `sb week` (runs after every `sb` command): don't edit by hand. "
           "AI agents: don't read this file.", ""]
    if older:
        out += ["## Last Week", "", "Open tasks from before this week.", "",
                "```tasks", "not done", "path includes Projects/", f"happens before {monday}",
                "sort by happens", "group by folder", "group by heading", "hide backlink", "```", ""]
    for i in range(7):
        d = monday + dt.timedelta(days=i)
        out += [f"## {d:%A} {d.day} {d:%b}" + (" (today)" if d == today else ""), ""]
        out += week_block(d, today)
    return "\n".join(out)


def cmd_week(a=None):
    monday = TODAY - dt.timedelta(days=TODAY.weekday())
    pages = {"Week.md": week_page("Week", monday, TODAY, older=True),
             "Week+1.md": week_page("Week+1", monday + dt.timedelta(days=7), TODAY)}
    for name, text in pages.items():
        path = ROOT / name
        old = path.read_bytes().decode("utf-8") if path.exists() else None
        if old is None or old.replace("\r\n", "\n") != text:
            path.write_bytes(text.encode("utf-8"))
            if a is not None:
                print(f"Wrote {name}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="sb", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add-task", help="append an open task (default project: general)")
    s.add_argument("text", nargs="+")
    s.add_argument("-p", "--project")
    s.add_argument("--due", help="YYYY-MM-DD")
    s.add_argument("--scheduled", help="YYYY-MM-DD")
    s.add_argument("--priority", choices=PRIORITIES)
    s.add_argument("--recur", help="e.g. 'every week'")
    s.add_argument("-s", "--sub", help="subproject within the project (created if new)")
    s.set_defaults(func=cmd_add_task)

    s = sub.add_parser("add-idea", help="append an idea to Ideas/<to>.md or a project's ideas.md")
    s.add_argument("text", nargs="+")
    g = s.add_mutually_exclusive_group()
    g.add_argument("-p", "--project")
    g.add_argument("--to", default="inbox", metavar="TOPIC", help="Ideas/<TOPIC>.md (default inbox; created if new)")
    s.set_defaults(func=cmd_add_idea)

    s = sub.add_parser("add-project", help="create Projects/<slug>/ with description.md and tasks.md")
    s.add_argument("slug")
    s.add_argument("--type", required=True, help="e.g. app, general")
    s.add_argument("--description", required=True)
    s.add_argument("--task", help="optional first task")
    s.add_argument("--priority", dest="project_priority", choices=["1", "2", "3"], help="1 = highest")
    s.add_argument("--goal", help="one line: why this project matters")
    s.set_defaults(func=cmd_add_project)

    s = sub.add_parser("add-note", help="create (or append to) Projects/<slug>/notes/<title>.md")
    s.add_argument("title")
    s.add_argument("-p", "--project", required=True)
    s.add_argument("-b", "--body", help="text (may be multi-line)")
    s.add_argument("-i", "--item", action="append", help="bullet line; repeatable")
    s.set_defaults(func=cmd_add_note)

    s = sub.add_parser("open", help="open tasks, numbered, for given projects (default: all non-done)")
    s.add_argument("projects", nargs="*")
    s.add_argument("--due", type=int, metavar="DAYS", help="only tasks due/scheduled within DAYS (incl. overdue)")
    s.add_argument("--stale", type=int, metavar="DAYS", help="only undated tasks created DAYS or more ago")
    s.set_defaults(func=cmd_open)

    s = sub.add_parser("show", help="open and done tasks of one project")
    s.add_argument("project")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("done", help="complete an open task by number (from `open`) or unique text match")
    s.add_argument("project")
    s.add_argument("match", nargs="+")
    s.set_defaults(func=cmd_done)

    s = sub.add_parser("move", help="move an open task to a subproject ('main' = no subproject), optionally of another project")
    s.add_argument("project")
    s.add_argument("sub")
    s.add_argument("match", nargs="+", help="number (from `open`) or unique text")
    s.add_argument("--to", metavar="PROJECT", help="move to this project instead (sub is then one of its subprojects)")
    s.set_defaults(func=cmd_move)

    s = sub.add_parser("cancel", help="cancel an open task (- [-] with ❌ date, archived; no next 🔁 occurrence)")
    s.add_argument("project")
    s.add_argument("match", nargs="+", help="number (from `open`) or unique text")
    s.set_defaults(func=cmd_cancel)

    s = sub.add_parser("edit", help="replace the description of an open task, keeping its dates, priority and recurrence")
    s.add_argument("project")
    s.add_argument("match", nargs="+", help="number (from `open`) or unique text")
    s.add_argument("-t", "--text", required=True, help="new description (without dates/priority)")
    s.set_defaults(func=cmd_edit)

    s = sub.add_parser("due", help="set or clear (date 'none') the 📅 due date of an open task, or of all due before --before")
    s.add_argument("project")
    s.add_argument("date", help="YYYY-MM-DD or 'none'")
    s.add_argument("match", nargs="*", help="number (from `open`) or unique text")
    s.add_argument("--before", metavar="DATE", help="instead of one task: every open task due before DATE")
    s.set_defaults(func=cmd_due)

    s = sub.add_parser("schedule", help="set or clear (date 'none') the ⏳ scheduled date (the day to work on it) of an open task, or of all scheduled before --before")
    s.add_argument("project")
    s.add_argument("date", help="YYYY-MM-DD or 'none'")
    s.add_argument("match", nargs="*", help="number (from `open`) or unique text")
    s.add_argument("--before", metavar="DATE", help="instead of one task: every open task scheduled before DATE")
    s.set_defaults(func=cmd_due, field=SCHEDULED)

    s = sub.add_parser("add-sub", help="create an (empty) subproject in a project")
    s.add_argument("project")
    s.add_argument("name", nargs="+")
    s.set_defaults(func=cmd_add_sub)

    s = sub.add_parser("archive", help="move ticked tasks from tasks.md to archive.md")
    s.add_argument("projects", nargs="*")
    s.set_defaults(func=cmd_archive)

    s = sub.add_parser("lint", help="check format; --fix archives ticked tasks and fills missing ➕ dates")
    s.add_argument("--fix", action="store_true")
    s.set_defaults(func=cmd_lint)

    s = sub.add_parser("overview", help="one line per project: counts and top next task")
    s.add_argument("--all", action="store_true", help="include done projects")
    s.add_argument("--idle", type=int, default=14, metavar="DAYS", help="flag active projects idle longer (default 14)")
    s.set_defaults(func=cmd_overview)

    s = sub.add_parser("log", help="tasks completed in the last N days")
    s.add_argument("projects", nargs="*")
    s.add_argument("--days", type=int, default=7)
    s.set_defaults(func=cmd_log)

    s = sub.add_parser("week", help="regenerate Week.md and Week+1.md (Obsidian views, Monday to Sunday)")
    s.set_defaults(func=cmd_week)

    a = p.parse_args()
    a.func(a)
    if a.func is not cmd_week:
        cmd_week()


if __name__ == "__main__":
    main()
