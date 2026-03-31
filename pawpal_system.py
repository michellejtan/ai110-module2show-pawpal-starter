# pawpal_system.py
#
# This is the logic layer for PawPal+.
# All backend classes live here — Owner, Pet, Task, Scheduler, and ScheduledTask.
# The Streamlit UI in app.py imports from this file to power the app.
# No display or UI logic belongs here; this file is purely about data and behavior.

from dataclasses import dataclass, field
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
        """
        pass

    def mark_complete(self) -> None:
        """Set completed to True when the user finishes the task."""
        pass

    def reset(self) -> None:
        """Set completed back to False for recurring tasks (is_recurring == True).
        Should only be called on tasks where is_recurring is True — e.g. daily
        feeding or a morning walk. One-time tasks (is_recurring == False) should
        not be reset.
        """
        pass


# ---------------------------------------------------------------------------
# Pet
# Represents a pet belonging to an owner.
# Holds identifying information (name, species, age, breed) and owns
# a list of care Tasks. Provides methods to add, view, and filter tasks.
# Used by: Owner (stores a list of Pets), Scheduler (reads pending tasks)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str                        # e.g. "dog", "cat"
    age: int
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        pass

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet, both complete and incomplete."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks where completed == False.
        This is what the Scheduler uses to build the daily plan —
        already-completed tasks are excluded automatically.
        """
        pass


# ---------------------------------------------------------------------------
# Owner
# Represents the person using the app.
# Holds identifying info (name, phone), their available time budget for
# the day, and manages a list of Pets.
# Used by: Scheduler (accesses owner.pets to find tasks across all pets)
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, phone: str, available_minutes: int):
        self.name = name
        self.phone = phone
        self.available_minutes = available_minutes  # total free minutes today
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's list of pets."""
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet from the list by name."""
        pass

    def find_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up and return a Pet by name.
        Returns None if no pet with that name is found.
        Used by the Scheduler to retrieve a specific pet's tasks.
        """
        pass

    def get_all_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across every pet this owner has.
        Loops through all pets, calls get_pending_tasks() on each,
        and returns a single flat list. Useful for a full dashboard view
        of everything that still needs to be done today.
        """
        pass


# ---------------------------------------------------------------------------
# ScheduledTask
# Represents the result of scheduling one Task.
# Wraps a Task object with a time slot (start_time) and a reason explaining
# why it was scheduled or skipped. Produced by Scheduler.build_plan().
# start_time is None when the task could not fit in the available time budget.
# Used by: Scheduler (creates these), app.py (displays these)
# ---------------------------------------------------------------------------

class ScheduledTask:
    def __init__(self, task: Task, start_time: Optional[str], reason: str):
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
        pass


# ---------------------------------------------------------------------------
# Scheduler
# The brain of the app. Given an Owner, it retrieves, organizes, and plans
# care tasks for a specific pet based on available time and priority.
# Produces a list of ScheduledTask objects representing the daily plan.
# Used by: app.py (creates a Scheduler and calls build_plan / explain_plan)
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    @property
    def available_minutes(self) -> int:
        """Always read available time directly from the owner.
        This ensures the Scheduler stays in sync if the owner's time changes.
        """
        return self.owner.available_minutes

    def get_tasks_by_pet(self, pet_name: str) -> list[Task]:
        """Use owner.find_pet() to retrieve pending tasks for one specific pet.
        Returns an empty list if the pet is not found.
        """
        pet = self.owner.find_pet(pet_name)
        if pet is None:
            return []
        return pet.get_pending_tasks()

    def build_plan(self, pet_name: str, start_time: str = "9:00 AM") -> list[ScheduledTask]:
        """Build a prioritized daily plan for the given pet.

        start_time sets the anchor for the first task (default: "9:00 AM").
        Each subsequent task's start time is calculated by adding the previous
        task's duration_minutes to the current time.

        Steps:
        1. Fetch pending tasks via get_tasks_by_pet(pet_name)
        2. Sort by priority_value() descending; use duration as tiebreak (shorter first)
        3. Walk through sorted tasks, adding each one if it fits in remaining time
        4. Assign start times sequentially to tasks that fit, starting from start_time
        5. Mark tasks that don't fit as skipped (start_time=None)
        6. Return a list of ScheduledTask objects (scheduled + skipped)
        """
        pass

    def explain_plan(self, pet_name: str) -> str:
        """Format the daily plan as a human-readable string for display.

        Calls build_plan(pet_name) and joins each ScheduledTask's summary()
        into a full schedule, e.g.:

            Daily plan for Mochi (45 min available):

            9:00 AM | Morning walk (20 min) [high] — Highest priority task.
            9:20 AM | Give medication (10 min) [high] — High priority, fits in remaining time.
            SKIPPED | Enrichment play (30 min) [medium] — Not enough time remaining (5 min left).
        """
        pass
