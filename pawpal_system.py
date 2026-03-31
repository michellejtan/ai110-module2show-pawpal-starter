# pawpal_system.py
#
# This is the logic layer for PawPal+.
# All backend classes live here — Owner, Pet, Task, Scheduler, and ScheduledTask.
# The Streamlit UI in app.py imports from this file to power the app.
# No display or UI logic belongs here; this file is purely about data and behavior.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# Represents a single pet care task (e.g., "Morning walk", "Give medication").
# Holds everything about what needs to be done: how long it takes, how urgent
# it is, when it's due, and whether it has been completed.
# Used by: Pet (stores a list of Tasks), Scheduler (reads and sorts Tasks)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care task with priority, duration, and completion state."""

    title: str                          # e.g. "Morning walk"
    task_type: str                      # e.g. "walk", "feeding", "medication"
    duration_minutes: int               # estimated time to complete
    priority: str                       # "low", "medium", or "high"
    due_time: str                       # e.g. "9:00 AM"
    completed: bool = False             # defaults to not completed
    is_recurring: bool = False          # if True, task can be reset daily (e.g. feeding)

    def priority_value(self) -> int:
        """Return a numeric value for priority to enable sorting.

        high   → 3
        medium → 2
        low    → 1
        Defaults to 0 for any unrecognised priority string.
        """
        mapping = {"high": 3, "medium": 2, "low": 1}
        return mapping.get(self.priority.lower(), 0)

    def mark_complete(self) -> None:
        """Set completed to True when the user finishes the task."""
        self.completed = True

    def reset(self) -> None:
        """Set completed back to False for recurring tasks (is_recurring == True).
        Should only be called on tasks where is_recurring is True — e.g. daily
        feeding or a morning walk. One-time tasks (is_recurring == False) should
        not be reset.
        """
        if self.is_recurring:
            self.completed = False


# ---------------------------------------------------------------------------
# Pet
# Represents a pet belonging to an owner.
# Holds identifying information (name, species, age, breed) and owns
# a list of care Tasks. Provides methods to add, view, and filter tasks.
# Used by: Owner (stores a list of Pets), Scheduler (reads pending tasks)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet with identifying info and an owned list of care Tasks."""

    name: str
    species: str                        # e.g. "dog", "cat"
    age: int
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> None:
        """Remove a task from this pet's task list by title.
        Does nothing if no task with that title is found.
        """
        self.tasks = [t for t in self.tasks if t.title != task_title]

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet, both complete and incomplete."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks where completed == False.
        This is what the Scheduler uses to build the daily plan —
        already-completed tasks are excluded automatically.
        """
        return [task for task in self.tasks if not task.completed]


# ---------------------------------------------------------------------------
# Owner
# Represents the person using the app.
# Holds identifying info (name, phone), their available time budget for
# the day, and manages a list of Pets.
# Used by: Scheduler (accesses owner.pets to find tasks across all pets)
# ---------------------------------------------------------------------------

class Owner:
    """Represents the app user, their contact info, time budget, and list of pets."""

    def __init__(self, name: str, phone: str, available_minutes: int):
        """Initialize an Owner with contact info and daily available time budget."""
        self.name = name
        self.phone = phone
        self.available_minutes = available_minutes  # total free minutes today
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet from the list by name.
        Does nothing if no pet with that name is found.
        """
        self.pets = [p for p in self.pets if p.name != pet_name]

    def find_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up and return a Pet by name.
        Returns None if no pet with that name is found.
        Used by the Scheduler to retrieve a specific pet's tasks.
        """
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across every pet this owner has.
        Loops through all pets, calls get_pending_tasks() on each,
        and returns a single flat list. Useful for a full dashboard view
        of everything that still needs to be done today.
        """
        pending = []
        for pet in self.pets:
            pending.extend(pet.get_pending_tasks())
        return pending


# ---------------------------------------------------------------------------
# ScheduledTask
# Represents the result of scheduling one Task.
# Wraps a Task object with a time slot (start_time) and a reason explaining
# why it was scheduled or skipped. Produced by Scheduler.build_plan().
# start_time is None when the task could not fit in the available time budget.
# Used by: Scheduler (creates these), app.py (displays these)
# ---------------------------------------------------------------------------

class ScheduledTask:
    """Wraps a Task with a scheduled start time and a reason; start_time is None if skipped."""

    def __init__(self, task: Task, start_time: Optional[str], reason: str):
        """Wrap a Task with its assigned start time and scheduling reason."""
        self.task = task
        self.start_time = start_time    # None means the task was skipped
        self.reason = reason

    def summary(self) -> str:
        """Return one human-readable line describing this scheduled or skipped task.

        Example (scheduled):
            9:00 AM | Morning walk (20 min) [high] — Highest priority task.
        Example (skipped):
            SKIPPED | Enrichment play (30 min) [medium] — Not enough time remaining (5 min left).
        """
        label = self.start_time if self.start_time else "SKIPPED"
        return (
            f"{label} | {self.task.title} "
            f"({self.task.duration_minutes} min) "
            f"[{self.task.priority}] — {self.reason}"
        )


# ---------------------------------------------------------------------------
# Scheduler
# The brain of the app. Given an Owner, it retrieves, organizes, and plans
# care tasks for a specific pet based on available time and priority.
# Produces a list of ScheduledTask objects representing the daily plan.
# Used by: app.py (creates a Scheduler and calls build_plan / explain_plan)
# ---------------------------------------------------------------------------

class Scheduler:
    """Builds and formats a prioritized daily care plan for a pet given an Owner's time budget."""

    def __init__(self, owner: Owner):
        """Initialize the Scheduler with an Owner whose pets and tasks will be planned."""
        self.owner = owner

    @property
    def available_minutes(self) -> int:
        """Return the owner's available minutes, staying in sync if it changes."""
        return self.owner.available_minutes

    def get_tasks_by_pet(self, pet_name: str) -> list[Task]:
        """Use owner.find_pet() to retrieve pending tasks for one specific pet.
        Returns an empty list if the pet is not found.
        """
        pet = self.owner.find_pet(pet_name)
        if pet is None:
            return []
        return pet.get_pending_tasks()

    def build_plan(self, pet_name: str, start_time: str = "8:00 AM") -> list[ScheduledTask]:
        """Build a prioritized daily plan for the given pet.

        start_time is the earliest the owner is available. Tasks due before
        start_time are skipped automatically. Among reachable tasks, budget is
        allocated by priority (high tasks claim time first) so a later high-priority
        task is never crowded out by an earlier low-priority one. Results are
        displayed in due_time order so the output reads as a chronological day plan.

        Steps:
        1. Fetch pending tasks via get_tasks_by_pet(pet_name)
        2. Skip any task whose due_time is before start_time
        3. Sort remaining tasks by priority_value() descending to allocate budget
        4. Walk through priority-sorted tasks, marking each scheduled or skipped
        5. Re-sort results by due_time ascending for chronological display
        6. Return a list of ScheduledTask objects (scheduled + skipped)
        """
        tasks = self.get_tasks_by_pet(pet_name)
        if not tasks:
            return []

        def parse_due(t):
            try:
                return datetime.strptime(t.due_time, "%I:%M %p")
            except (ValueError, AttributeError):
                return datetime.max

        owner_start = datetime.strptime(start_time, "%I:%M %p")

        # Step 1: fetch pending tasks — done above via get_tasks_by_pet

        # Step 2: separate tasks into reachable and too-early
        too_early = []
        reachable = []
        for task in tasks:
            if parse_due(task) < owner_start:
                too_early.append(task)
            else:
                reachable.append(task)

        scheduled = []

        # Mark too-early tasks as skipped
        for task in too_early:
            scheduled.append(ScheduledTask(
                task, None,
                f"Due at {task.due_time}, before owner is available ({start_time})."
            ))

        # Step 3: sort remaining tasks by priority_value() descending to allocate budget
        # Step 4: walk through priority-sorted tasks, marking each scheduled or skipped
        by_priority = sorted(reachable, key=lambda t: (-t.priority_value(), t.duration_minutes))
        remaining_minutes = self.available_minutes

        for task in by_priority:
            if task.duration_minutes <= remaining_minutes:
                reason = (
                    f"High priority — scheduled at its due time ({remaining_minutes} min remaining in day)."
                    if task.priority == "high"
                    else f"Scheduled at its due time ({remaining_minutes} min remaining in day)."
                )
                scheduled.append(ScheduledTask(task, task.due_time, reason))
                remaining_minutes -= task.duration_minutes
            else:
                scheduled.append(ScheduledTask(
                    task, None,
                    f"Not enough time remaining "
                    f"({remaining_minutes} min left, needs {task.duration_minutes} min)."
                ))

        # Step 5: re-sort for chronological display (skipped tasks go to the end)
        scheduled.sort(key=lambda s: parse_due(s.task) if s.start_time else datetime.max)

        return scheduled

    def explain_plan(self, pet_name: str, start_time: str = "8:00 AM") -> str:
        """Format the daily plan as a human-readable string for display.

        Calls build_plan(pet_name, start_time) and joins each ScheduledTask's
        summary() into a full schedule, e.g.:

            Daily plan for Mochi (90 min available, starting 8:00 AM):

            8:00 AM | Morning walk (20 min) [high] — High priority — scheduled at its due time.
            9:00 AM | Give medication (10 min) [high] — High priority — scheduled at its due time.
            SKIPPED | Enrichment play (30 min) [medium] — Not enough time remaining (5 min left, needs 30 min).
        """
        plan = self.build_plan(pet_name, start_time)

        if not plan:
            return f"No pending tasks found for {pet_name}."

        lines = [f"Daily plan for {pet_name} ({self.available_minutes} min available, starting {start_time}):\n"]
        for scheduled_task in plan:
            lines.append(scheduled_task.summary())

        return "\n".join(lines)
