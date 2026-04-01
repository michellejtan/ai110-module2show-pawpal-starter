# main.py
# Temporary testing ground — verifies PawPal+ logic works end-to-end in the terminal.
# Not production code; for demo and development use only.

from pawpal_system import Owner, Pet, Task, Scheduler

# ── Setup ────────────────────────────────────────────────────────────────────

owner = Owner(name="Jamie", phone="555-0100", available_minutes=90)

# Pet 1: Mochi the dog — tasks added out of order intentionally
mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
mochi.add_task(Task(
    title="Enrichment play session",
    task_type="play",
    duration_minutes=45,
    priority="low",
    due_time="11:00 AM",
))
mochi.add_task(Task(
    title="Give heartworm medication",
    task_type="medication",
    duration_minutes=5,
    priority="high",
    due_time="9:00 AM",
))
mochi.add_task(Task(
    title="Morning walk",
    task_type="walk",
    duration_minutes=30,
    priority="high",
    due_time="8:00 AM",
    frequency="daily",
))
mochi.add_task(Task(
    title="Breakfast feeding",
    task_type="feeding",
    duration_minutes=10,
    priority="medium",
    due_time="8:30 AM",
    frequency="daily",
))

# Intentional conflict: same due_time as "Give heartworm medication" (9:00 AM)
mochi.add_task(Task(
    title="Weigh-in check",
    task_type="health",
    duration_minutes=5,
    priority="medium",
    due_time="9:00 AM",
))

# Pet 2: Luna the cat
luna = Pet(name="Luna", species="cat", age=5, breed="Domestic Shorthair")
luna.add_task(Task(
    title="Clean litter box",
    task_type="hygiene",
    duration_minutes=10,
    priority="high",
    due_time="8:00 AM",
    frequency="daily",
))
luna.add_task(Task(
    title="Breakfast feeding",
    task_type="feeding",
    duration_minutes=5,
    priority="medium",
    due_time="8:15 AM",
    frequency="daily",
))
luna.add_task(Task(
    title="Brush coat",
    task_type="grooming",
    duration_minutes=15,
    priority="low",
    due_time="10:00 AM",
))

owner.add_pet(mochi)
owner.add_pet(luna)

# ── Print Today's Schedule ───────────────────────────────────────────────────

scheduler = Scheduler(owner)

print("=" * 60)
print("  Conflict Detection:")
print("-" * 60)
for pet in owner.pets:
    warning = scheduler.conflict_summary(pet.name)
    print(f"  {warning if warning else f'✓ No conflicts for {pet.name}'}")
print("=" * 60)

print("=" * 60)
print(f"  PawPal+ — TODAY'S SCHEDULE")
print(f"  Owner : {owner.name}  |  Available time: {owner.available_minutes} min")
print("=" * 60)

for pet in owner.pets:
    print()
    print(f"  {pet.name} ({pet.breed}, {pet.age} yr old {pet.species})")
    print("-" * 60)
    plan_text = scheduler.explain_plan(pet.name, start_time="8:30 AM")
    # Indent each line for readability
    for line in plan_text.splitlines():
        print(f"  {line}")

print()
print("=" * 60)
print("  All pending tasks across all pets:")
print("-" * 60)
all_pending = owner.get_all_pending_tasks()
for task in all_pending:
    status = "[done]" if task.completed else "[ ]  "
    print(f"  {status} {task.due_time:<10} {task.title:<35} ({task.duration_minutes} min, {task.priority})")
print("=" * 60)

# ── Recurring task auto-creation demo ────────────────────────────────────────

print()
print("=" * 60)
print("  mark_task_complete() — completing Mochi's Morning walk:")
print("-" * 60)
next_task = scheduler.mark_task_complete("Mochi", "Morning walk")
if next_task:
    print(f"  Marked complete. Next occurrence created:")
    print(f"  → '{next_task.title}' due on {next_task.due_date} at {next_task.due_time} (frequency: {next_task.frequency})")
print("=" * 60)

# ── Sort & Filter demos ───────────────────────────────────────────────────────

print()
print("=" * 60)
print("  sort_by_time() — all tasks across all pets sorted by due time:")
print("-" * 60)
sorted_tasks = scheduler.sort_by_time(owner.get_all_pending_tasks())
for task in sorted_tasks:
    print(f"  {task.due_time:<10} {task.title}")

print()
print("=" * 60)
print("  filter_tasks(completed=False) — all pending tasks:")
print("-" * 60)
pending = scheduler.filter_tasks(completed=False)
for task in pending:
    print(f"  [ ]  {task.due_time:<10} {task.title}")

print()
print("=" * 60)
print("  filter_tasks(pet_name='Luna') — all of Luna's tasks:")
print("-" * 60)
luna_tasks = scheduler.filter_tasks(pet_name="Luna")
for task in luna_tasks:
    print(f"  {task.due_time:<10} {task.title}")

print()
print("=" * 60)
print("  filter_tasks(completed=False, pet_name='Mochi') — Mochi's pending tasks:")
print("-" * 60)
mochi_pending = scheduler.filter_tasks(completed=False, pet_name="Mochi")
for task in mochi_pending:
    print(f"  [ ]  {task.due_time:<10} {task.title}")
print("=" * 60)
