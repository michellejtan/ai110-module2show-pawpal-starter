# main.py
# Temporary testing ground — verifies PawPal+ logic works end-to-end in the terminal.
# Not production code; for demo and development use only.

from pawpal_system import Owner, Pet, Task, Scheduler

# ── Setup ────────────────────────────────────────────────────────────────────

owner = Owner(name="Jamie", phone="555-0100", available_minutes=90)

# Pet 1: Mochi the dog
mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
mochi.add_task(Task(
    title="Morning walk",
    task_type="walk",
    duration_minutes=30,
    priority="high",
    due_time="8:00 AM",
    is_recurring=True,
))
mochi.add_task(Task(
    title="Give heartworm medication",
    task_type="medication",
    duration_minutes=5,
    priority="high",
    due_time="9:00 AM",
))
mochi.add_task(Task(
    title="Breakfast feeding",
    task_type="feeding",
    duration_minutes=10,
    priority="medium",
    due_time="8:30 AM",
    is_recurring=True,
))
mochi.add_task(Task(
    title="Enrichment play session",
    task_type="play",
    duration_minutes=45,
    priority="low",
    due_time="11:00 AM",
))

# Pet 2: Luna the cat
luna = Pet(name="Luna", species="cat", age=5, breed="Domestic Shorthair")
luna.add_task(Task(
    title="Clean litter box",
    task_type="hygiene",
    duration_minutes=10,
    priority="high",
    due_time="8:00 AM",
    is_recurring=True,
))
luna.add_task(Task(
    title="Breakfast feeding",
    task_type="feeding",
    duration_minutes=5,
    priority="medium",
    due_time="8:15 AM",
    is_recurring=True,
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
