---
cssclasses: section-headers
---
# Today

Obsidian-only focus view (Tasks plugin). AI agents: don't read this file. Plan days with `sb schedule <proj> <date> <task>`.

## Today

Due or scheduled today. Ticked tasks stay visible until tomorrow, but only if they were due or scheduled today.

```tasks
happens today
path includes Projects/
sort by done
sort by priority
group by folder
group by heading
hide backlink
```

## Overdue

Open tasks from earlier days. They disappear once ticked; reschedule or clear the date on the ones you won't do soon.

```tasks
not done
path includes Projects/
happens before today
sort by happens
group by folder
group by heading
hide backlink
```
