---
cssclasses: section-headers
---
# Dashboard

Live views for Obsidian (Bases + Tasks plugin). AI agents: don't read this file — use `python tools/sb.py overview`.

## Projects

```base
filters:
  and:
    - file.inFolder("Projects")
    - file.basename == "description"
formulas:
  project: file.asLink(file.folder.replace("Projects/", ""))
properties:
  formula.project:
    displayName: Project
views:
  - type: table
    name: Active & paused
    filters:
      and:
        - status != "done"
    order:
      - formula.project
      - status
      - priority
      - type
      - goal
      - started
    sort:
      - property: priority
        direction: ASC
  - type: table
    name: All
    order:
      - formula.project
      - status
      - priority
      - type
      - goal
      - started
    groupBy:
      property: status
      direction: ASC
```

## Overdue & today

```tasks
not done
path includes Projects/
happens before tomorrow
sort by happens
group by folder
group by heading
hide backlink
```

## Next 7 days

```tasks
not done
path includes Projects/
happens after today
happens before in 8 days
sort by happens
group by folder
group by heading
hide backlink
```

## High priority

```tasks
not done
path includes Projects/
priority is above medium
sort by priority
group by folder
group by heading
hide backlink
```

## All open tasks

```tasks
not done
path includes Projects/
sort by priority
group by folder
group by heading
hide backlink
short mode
```

## Stale (30+ days, no date)

```tasks
not done
path includes Projects/
created before 30 days ago
no due date
no scheduled date
group by folder
group by heading
hide backlink
short mode
```

## Done in the last 7 days

```tasks
done
done after 8 days ago
sort by done reverse
group by folder
group by heading
hide backlink
short mode
```
