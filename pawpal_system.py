# pawpal_system.py
#
# This is the logic layer for PawPal+.
# All backend classes live here — Owner, Pet, Task, Scheduler, and ScheduledTask.
# The Streamlit UI in app.py imports from this file to power the app.
# No display or UI logic belongs here; this file is purely about data and behavior.

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
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
    frequency: Optional[str] = None    # "daily", "weekly", or None for one-time tasks
    due_date: Optional[date] = None    # calendar date the task is due (date object)

    def priority_value(self) -> int:
        """Return a numeric value for priority to enable sorting.

        Returns:
            3 for "high", 2 for "medium", 1 for "low", 0 for any unrecognised string.
        """
        mapping = {"high": 3, "medium": 2, "low": 1}
        return mapping.get(self.priority.lower(), 0)

    def mark_complete(self) -> None:
        """Set completed to True when the user finishes the task."""
        self.completed = True

    def next_occurrence(self) -> "Task":
        """Return a new Task representing the next scheduled occurrence of this task.

        Uses Python's timedelta to calculate the next due_date accurately:
        - "daily"  → due_date = today + 1 day
        - "weekly" → due_date = today + 7 days

        The new task is identical to this one except completed is reset to False
        and due_date is updated. Should only be called on tasks where frequency
        is "daily" or "weekly".

        Returns:
            A new Task instance for the next occurrence, with completed=False.

        Raises:
            ValueError: if frequency is None (one-time tasks have no next occurrence).
        """
        if self.frequency == "daily":
            next_date = date.today() + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = date.today() + timedelta(days=7)
        else:
            raise ValueError(
                f"Cannot create next occurrence for task '{self.title}': "
                f"frequency is None (one-time task)."
            )
        return Task(
            title=self.title,
            task_type=self.task_type,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            due_time=self.due_time,
            completed=False,
            frequency=self.frequency,
            due_date=next_date,
        )

    def reset(self) -> None:
        """Set completed back to False for recurring tasks only.

        Should only be called on tasks where frequency is set — e.g. daily
        feeding or a morning walk. One-time tasks (frequency == None) are
        silently ignored.
        """
        if self.frequency is not None:
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

        Args:
            task_title: the title of the task to remove. Does nothing if no
                        task with that title is found.
        """
        self.tasks = [t for t in self.tasks if t.title != task_title]

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet, both complete and incomplete."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks where completed == False.

        This is what the Scheduler uses to build the daily plan —
        already-completed tasks are excluded automatically.

        Returns:
            A list of Task objects where completed is False.
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

        Args:
            pet_name: the name of the pet to remove. Does nothing if no pet
                      with that name is found.
        """
        self.pets = [p for p in self.pets if p.name != pet_name]

    def find_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up and return a Pet by name.

        Used by the Scheduler to retrieve a specific pet's tasks.

        Args:
            pet_name: the name of the pet to search for.

        Returns:
            The matching Pet object, or None if no pet with that name is found.
        """
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across every pet this owner has.

        Loops through all pets and calls get_pending_tasks() on each,
        returning a single flat list. Useful for a full dashboard view
        of everything that still needs to be done today.

        Returns:
            A flat list of Task objects where completed is False, across all pets.
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

        Returns:
            A formatted string with the start time (or SKIPPED), task title,
            duration, priority, and scheduling reason.

        Example:
            "9:00 AM | Morning walk (20 min) [high] — High priority task."
            "SKIPPED | Enrichment play (30 min) [medium] — Not enough time remaining (5 min left)."
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
        """Retrieve pending tasks for one specific pet via owner.find_pet().

        Args:
            pet_name: the name of the pet whose pending tasks to retrieve.

        Returns:
            A list of pending Task objects for the pet, or an empty list if
            the pet is not found.
        """
        pet = self.owner.find_pet(pet_name)
        if pet is None:
            return []
        return pet.get_pending_tasks()

    def find_conflicts(self, pet_name: str) -> list[tuple[Task, Task]]:
        """Detect tasks assigned to the same due_time for a given pet.

        Scans pending tasks for the pet and collects any pair that shares an
        identical due_time string. Returns a list of (task_a, task_b) pairs —
        an empty list means no conflicts were found. Does not raise an exception
        so the program keeps running regardless of what is found.

        Args:
            pet_name: name of the pet to check.

        Returns:
            A list of (task_a, task_b) tuples where both tasks share a due_time.
            Empty list if no conflicts exist or the pet is not found.
        """
        tasks = self.get_tasks_by_pet(pet_name)
        seen: dict[str, Task] = {}
        conflicts: list[tuple[Task, Task]] = []
        for task in tasks:
            if task.due_time in seen:
                conflicts.append((seen[task.due_time], task))
            else:
                seen[task.due_time] = task
        return conflicts

    def conflict_summary(self, pet_name: str) -> str:
        """Return a human-readable warning string listing all due_time conflicts for a pet.

        Calls find_conflicts() and formats the results into a printable message.
        Returns an empty string when there are no conflicts, so callers can use
        a simple truthiness check before printing.

        Args:
            pet_name: name of the pet to check.

        Returns:
            A formatted warning string listing each conflict, or an empty string
            if no conflicts were detected.

        Example output:
            ⚠ Conflicts for Mochi:
              'Give heartworm medication' and 'Weigh-in check' are both due at 9:00 AM
        """
        conflicts = self.find_conflicts(pet_name)
        if not conflicts:
            return ""
        lines = [f"⚠ Conflicts for {pet_name}:"]
        for a, b in conflicts:
            lines.append(f"  '{a.title}' and '{b.title}' are both due at {a.due_time}")
        return "\n".join(lines)

    def build_plan(self, pet_name: str, start_time: str = "8:00 AM") -> list[ScheduledTask]:
        """Build a prioritized daily plan for the given pet.

        Tasks due before start_time are skipped. Among reachable tasks, the
        time budget is allocated by priority (high first) so high-priority tasks
        are never crowded out by lower-priority ones. Results are sorted by
        due_time so the output reads as a chronological day plan.

        Args:
            pet_name:   name of the pet to build the plan for.
            start_time: earliest time the owner is available (default "8:00 AM").

        Returns:
            A chronologically sorted list of ScheduledTask objects, each either
            assigned a start time or marked as skipped with a reason.
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

    def mark_task_complete(self, pet_name: str, task_title: str) -> Optional[Task]:
        """Mark a task complete and automatically schedule its next occurrence.

        Finds the first incomplete task matching task_title for the given pet,
        marks it complete, then checks its frequency:
        - "daily"  → creates a new Task due tomorrow (today + 1 day via timedelta)
        - "weekly" → creates a new Task due next week (today + 7 days via timedelta)
        - None     → one-time task; no new instance is created

        The next occurrence is added directly to the pet's task list so it
        appears in future plans without any extra steps.

        Args:
            pet_name:   Name of the pet whose task should be marked complete.
            task_title: Title of the task to mark complete.

        Returns:
            The newly created Task for the next occurrence, or None if the task
            is one-time or if the pet / task could not be found.
        """
        pet = self.owner.find_pet(pet_name)
        if pet is None:
            return None

        for task in pet.tasks:
            if task.title == task_title and not task.completed:
                task.mark_complete()
                if task.frequency in ("daily", "weekly"):
                    next_task = task.next_occurrence()
                    pet.add_task(next_task)
                    return next_task
                return None

        return None

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted chronologically by due_time using a lambda key.

        Converts each due_time string (e.g. "9:00 AM") to a datetime so
        times are compared numerically, not alphabetically. Without this,
        "10:00 AM" would sort before "9:00 AM" because "1" < "9".

        Args:
            tasks: list of Task objects to sort (not mutated).

        Returns:
            A new list of Task objects sorted earliest due_time first.
        """
        def parse_time(t: Task) -> datetime:
            try:
                return datetime.strptime(t.due_time, "%I:%M %p")
            except (ValueError, AttributeError):
                return datetime.max

        return sorted(tasks, key=parse_time)

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[Task]:
        """Filter tasks across all pets by completion status, pet name, or both.

        Each argument is optional — omit it to skip that filter. Supplying
        both narrows the result to tasks that satisfy both conditions at once.

        Args:
            completed: True  → return only completed tasks.
                       False → return only pending (incomplete) tasks.
                       None  → completion status is not filtered (default).
            pet_name:  A pet's name → return only tasks belonging to that pet.
                       None         → include tasks from all pets (default).

        Returns:
            A flat list of Task objects matching every supplied filter.

        Examples:
            scheduler.filter_tasks()                          # all tasks, all pets
            scheduler.filter_tasks(completed=False)           # all pending tasks
            scheduler.filter_tasks(pet_name="Mochi")          # all of Mochi's tasks
            scheduler.filter_tasks(completed=False, pet_name="Mochi")  # Mochi's pending tasks
        """
        results: list[Task] = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results

    def explain_plan(self, pet_name: str, start_time: str = "8:00 AM") -> str:
        """Format the daily plan as a human-readable string for display.

        Calls build_plan() and joins each ScheduledTask's summary() into a
        printable schedule showing what is planned, what is skipped, and why.

        Args:
            pet_name:   name of the pet to build the plan for.
            start_time: earliest time the owner is available (default "8:00 AM").

        Returns:
            A formatted multi-line string with a header and one line per task.

        Example:
            Daily plan for Mochi (90 min available, starting 8:00 AM):

            8:00 AM | Morning walk (20 min) [high] — High priority.
            SKIPPED | Enrichment play (30 min) [medium] — Not enough time remaining.
        """
        plan = self.build_plan(pet_name, start_time)

        if not plan:
            return f"No pending tasks found for {pet_name}."

        lines = [f"Daily plan for {pet_name} ({self.available_minutes} min available, starting {start_time}):\n"]
        for scheduled_task in plan:
            lines.append(scheduled_task.summary())

        return "\n".join(lines)
