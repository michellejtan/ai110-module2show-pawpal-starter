# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The scheduler goes beyond a basic plan — it can sort, filter, handle repeating tasks, and warn you when two things are scheduled at the same time.

### Sort by time
Tasks are automatically sorted by due time so the daily plan always reads in chronological order. If a task has a missing or unrecognized time, it gets pushed to the end instead of causing an error.
→ `Scheduler.sort_by_time(tasks)`

### Filter tasks
You can ask for a focused view of tasks — for example, only tasks that are still pending, only tasks for a specific pet, or both at once. This makes it easy to check what still needs to be done without scrolling through everything.
→ `Scheduler.filter_tasks(completed, pet_name)`

### Recurring tasks
Some tasks repeat every day or every week (like feeding or a morning walk). When you mark one of these complete, the scheduler automatically schedules the next occurrence on the right date — no manual re-entry needed.
→ `Scheduler.mark_task_complete(pet_name, task_title)` · `Task.next_occurrence()`

### Conflict detection
If two tasks for the same pet are due at the same time, the scheduler catches it and prints a warning before showing the daily plan. This helps you spot and fix scheduling overlaps early.
→ `Scheduler.find_conflicts(pet_name)` · `Scheduler.conflict_summary(pet_name)`
