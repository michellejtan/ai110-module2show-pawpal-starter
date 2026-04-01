import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should set completed to True."""
    # Arrange: create a task that starts as not completed
    task = Task(
        title="Morning walk",
        task_type="walk",
        duration_minutes=20,
        priority="high",
        due_time="9:00 AM",
        completed=False,
    )
    # Act: confirm initial state, then mark it complete
    assert task.completed is False
    task.mark_complete()
    # Assert: completed should now be True
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet should increase its task count by 1."""
    # Arrange: create a pet with no tasks and a task to add
    pet = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    task = Task(
        title="Give medication",
        task_type="medication",
        duration_minutes=5,
        priority="high",
        due_time="8:00 AM",
    )
    # Act: record the count before, then add the task
    initial_count = len(pet.tasks)
    pet.add_task(task)
    # Assert: task list should have grown by exactly one
    assert len(pet.tasks) == initial_count + 1


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner_with_pet():
    """Owner with one pet (Mochi) and no tasks — reused across all test groups."""
    owner = Owner(name="Jordan", phone="555-0000", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    owner.add_pet(pet)
    return owner


@pytest.fixture
def scheduler(owner_with_pet):
    """Scheduler bound to the owner_with_pet fixture."""
    return Scheduler(owner_with_pet)


def _task(title, due_time, duration=10, priority="medium", frequency=None):
    """Minimal Task builder — keeps test bodies focused on the scenario, not boilerplate."""
    return Task(
        title=title,
        task_type="general",
        duration_minutes=duration,
        priority=priority,
        due_time=due_time,
        frequency=frequency,
    )


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_basic_chronological_order(scheduler):
    """Tasks out of order should come back sorted earliest-first."""
    tasks = [
        _task("Late morning snack", "10:00 AM"),
        _task("Morning walk",       "9:00 AM"),
        _task("Early feeding",      "8:00 AM"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert [t.due_time for t in result] == ["8:00 AM", "9:00 AM", "10:00 AM"]


def test_sort_by_time_numeric_not_alphabetic(scheduler):
    """'10:00 AM' sorts before '9:00 AM' alphabetically — the sort must be numeric."""
    tasks = [
        _task("B", "10:00 AM"),
        _task("A", "9:00 AM"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert result[0].due_time == "9:00 AM"
    assert result[1].due_time == "10:00 AM"


def test_sort_by_time_am_before_pm(scheduler):
    """AM tasks must always appear before PM tasks regardless of hour numbers."""
    tasks = [
        _task("Afternoon walk", "1:00 PM"),
        _task("Late morning",   "11:00 AM"),
        _task("Early feeding",  "8:00 AM"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert [t.due_time for t in result] == ["8:00 AM", "11:00 AM", "1:00 PM"]


def test_sort_by_time_does_not_mutate_input(scheduler):
    """sort_by_time() must return a new list and leave the original order intact."""
    tasks = [_task("B", "10:00 AM"), _task("A", "8:00 AM")]
    original = [t.title for t in tasks]
    scheduler.sort_by_time(tasks)
    assert [t.title for t in tasks] == original


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_completion_adds_task_due_tomorrow(scheduler, owner_with_pet):
    """Completing a daily task should create one new pending task due tomorrow."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Morning feeding", "8:00 AM", frequency="daily"))

    scheduler.mark_task_complete("Mochi", "Morning feeding")

    tomorrow = date.today() + timedelta(days=1)
    pending = [t for t in pet.tasks if not t.completed]
    assert len(pending) == 1
    assert pending[0].due_date == tomorrow


def test_weekly_task_completion_adds_task_due_in_7_days(scheduler, owner_with_pet):
    """Completing a weekly task should create one new pending task due in 7 days."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Bath time", "10:00 AM", frequency="weekly"))

    scheduler.mark_task_complete("Mochi", "Bath time")

    next_week = date.today() + timedelta(days=7)
    pending = [t for t in pet.tasks if not t.completed]
    assert len(pending) == 1
    assert pending[0].due_date == next_week


def test_one_time_task_completion_adds_no_new_task(scheduler, owner_with_pet):
    """Completing a one-time task (frequency=None) should not grow the task list."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Vet appointment", "9:00 AM", frequency=None))

    result = scheduler.mark_task_complete("Mochi", "Vet appointment")

    assert result is None
    assert len(pet.tasks) == 1


def test_original_recurring_task_is_marked_done(scheduler, owner_with_pet):
    """After completion, the original task's completed flag must be True."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Evening walk", "6:00 PM", frequency="daily"))

    scheduler.mark_task_complete("Mochi", "Evening walk")

    assert pet.tasks[0].completed is True


def test_completing_unknown_pet_returns_none(scheduler):
    """mark_task_complete() must return None gracefully for a non-existent pet."""
    result = scheduler.mark_task_complete("Ghost", "Morning walk")
    assert result is None


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_find_conflicts_detects_same_due_time(scheduler, owner_with_pet):
    """Two tasks at the same due_time should appear as a conflict pair."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Morning walk",    "9:00 AM"))
    pet.add_task(_task("Give medication", "9:00 AM"))

    conflicts = scheduler.find_conflicts("Mochi")

    assert len(conflicts) == 1
    titles = {conflicts[0][0].title, conflicts[0][1].title}
    assert titles == {"Morning walk", "Give medication"}


def test_find_conflicts_no_conflicts_returns_empty_list(scheduler, owner_with_pet):
    """Unique due_times should produce no conflicts."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Morning walk",    "8:00 AM"))
    pet.add_task(_task("Give medication", "9:00 AM"))

    assert scheduler.find_conflicts("Mochi") == []


def test_conflict_summary_empty_string_when_no_conflicts(scheduler, owner_with_pet):
    """conflict_summary() should return '' so callers can use a simple truthiness check."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Morning walk", "8:00 AM"))

    assert scheduler.conflict_summary("Mochi") == ""


def test_conflict_summary_includes_task_titles_and_time(scheduler, owner_with_pet):
    """The conflict summary string must name both tasks and their shared time."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Walk",       "9:00 AM"))
    pet.add_task(_task("Medication", "9:00 AM"))

    summary = scheduler.conflict_summary("Mochi")

    assert "Walk" in summary
    assert "Medication" in summary
    assert "9:00 AM" in summary


def test_find_conflicts_unknown_pet_returns_empty_list(scheduler):
    """find_conflicts() should return [] gracefully when the pet is not found."""
    assert scheduler.find_conflicts("Ghost") == []


# ---------------------------------------------------------------------------
# Smarter scheduling (build_plan / explain_plan)
# ---------------------------------------------------------------------------

def test_build_plan_high_priority_scheduled_before_low(scheduler, owner_with_pet):
    """High-priority tasks must be scheduled even when the budget is tight."""
    owner_with_pet.available_minutes = 20
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Low priority task",  "9:00 AM", duration=15, priority="low"))
    pet.add_task(_task("High priority task", "9:30 AM", duration=20, priority="high"))

    plan = scheduler.build_plan("Mochi")
    scheduled_titles = [s.task.title for s in plan if s.start_time is not None]

    assert "High priority task" in scheduled_titles
    assert "Low priority task" not in scheduled_titles


def test_build_plan_skips_tasks_before_start_time(scheduler, owner_with_pet):
    """Tasks due before the owner's start time should be marked skipped."""
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Too early task", "6:00 AM", duration=10, priority="high"))

    plan = scheduler.build_plan("Mochi", start_time="8:00 AM")
    skipped = [s for s in plan if s.start_time is None]

    assert len(skipped) == 1
    assert skipped[0].task.title == "Too early task"


def test_build_plan_exact_budget_fit_is_scheduled(scheduler, owner_with_pet):
    """A task that uses exactly the remaining budget should be scheduled, not skipped."""
    owner_with_pet.available_minutes = 30
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Exact fit task", "9:00 AM", duration=30, priority="medium"))

    plan = scheduler.build_plan("Mochi")
    scheduled = [s for s in plan if s.start_time is not None]

    assert len(scheduled) == 1
    assert scheduled[0].task.title == "Exact fit task"


def test_build_plan_over_budget_task_is_skipped(scheduler, owner_with_pet):
    """A task that exceeds the remaining budget by even 1 minute must be skipped."""
    owner_with_pet.available_minutes = 29
    pet = owner_with_pet.find_pet("Mochi")
    pet.add_task(_task("Too long task", "9:00 AM", duration=30, priority="medium"))

    plan = scheduler.build_plan("Mochi")
    skipped = [s for s in plan if s.start_time is None]

    assert len(skipped) == 1


def test_build_plan_returns_empty_for_pet_with_no_tasks(scheduler):
    """build_plan() must return an empty list when the pet has no pending tasks."""
    assert scheduler.build_plan("Mochi") == []


def test_explain_plan_no_tasks_returns_message(scheduler):
    """explain_plan() must return a human-readable message (not crash) for empty task lists."""
    result = scheduler.explain_plan("Mochi")
    assert "Mochi" in result
    assert len(result) > 0


# ---------------------------------------------------------------------------
# filter_tasks
# ---------------------------------------------------------------------------

def test_filter_tasks_by_completed_true(scheduler, owner_with_pet):
    """filter_tasks(completed=True) should return only completed tasks."""
    pet = owner_with_pet.find_pet("Mochi")
    done = _task("Done task", "8:00 AM")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(_task("Pending task", "9:00 AM"))

    result = scheduler.filter_tasks(completed=True)

    assert len(result) == 1
    assert result[0].title == "Done task"


def test_filter_tasks_by_completed_false(scheduler, owner_with_pet):
    """filter_tasks(completed=False) should return only incomplete tasks."""
    pet = owner_with_pet.find_pet("Mochi")
    done = _task("Done task", "8:00 AM")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(_task("Pending task", "9:00 AM"))

    result = scheduler.filter_tasks(completed=False)

    assert len(result) == 1
    assert result[0].title == "Pending task"


def test_filter_tasks_by_pet_name(scheduler, owner_with_pet):
    """filter_tasks(pet_name=...) should return only tasks belonging to that pet."""
    owner_with_pet.add_pet(Pet(name="Boba", species="cat", age=2, breed="Tabby"))
    owner_with_pet.find_pet("Mochi").add_task(_task("Mochi task", "8:00 AM"))
    owner_with_pet.find_pet("Boba").add_task(_task("Boba task",  "9:00 AM"))

    result = scheduler.filter_tasks(pet_name="Mochi")

    assert len(result) == 1
    assert result[0].title == "Mochi task"


def test_filter_tasks_combined_completed_and_pet_name(scheduler, owner_with_pet):
    """filter_tasks(completed=False, pet_name=...) should apply both filters at once."""
    owner_with_pet.add_pet(Pet(name="Boba", species="cat", age=2, breed="Tabby"))

    done = _task("Done task", "8:00 AM")
    done.mark_complete()
    owner_with_pet.find_pet("Mochi").add_task(done)
    owner_with_pet.find_pet("Mochi").add_task(_task("Pending task", "9:00 AM"))
    owner_with_pet.find_pet("Boba").add_task(_task("Boba pending", "10:00 AM"))

    result = scheduler.filter_tasks(completed=False, pet_name="Mochi")

    assert len(result) == 1
    assert result[0].title == "Pending task"


def test_filter_tasks_unknown_pet_returns_empty(scheduler):
    """filter_tasks() for a non-existent pet name should return []."""
    assert scheduler.filter_tasks(pet_name="Ghost") == []


# ---------------------------------------------------------------------------
# Owner.get_all_pending_tasks and multi-pet scenarios
# ---------------------------------------------------------------------------

def test_get_all_pending_tasks_aggregates_across_pets(owner_with_pet):
    """get_all_pending_tasks() should return pending tasks from every pet combined."""
    owner_with_pet.add_pet(Pet(name="Boba", species="cat", age=2, breed="Tabby"))
    owner_with_pet.find_pet("Mochi").add_task(_task("Mochi walk",    "8:00 AM"))
    owner_with_pet.find_pet("Boba").add_task(_task("Boba feeding",   "9:00 AM"))

    pending = owner_with_pet.get_all_pending_tasks()

    titles = {t.title for t in pending}
    assert titles == {"Mochi walk", "Boba feeding"}


def test_get_all_pending_tasks_excludes_completed(owner_with_pet):
    """get_all_pending_tasks() must not include completed tasks from any pet."""
    done = _task("Done walk", "8:00 AM")
    done.mark_complete()
    owner_with_pet.find_pet("Mochi").add_task(done)
    owner_with_pet.find_pet("Mochi").add_task(_task("Pending task", "9:00 AM"))

    pending = owner_with_pet.get_all_pending_tasks()

    assert len(pending) == 1
    assert pending[0].title == "Pending task"


def test_multi_pet_conflicts_are_independent(owner_with_pet):
    """Conflicts for one pet should not bleed into another pet's conflict check."""
    owner_with_pet.add_pet(Pet(name="Boba", species="cat", age=2, breed="Tabby"))
    # Mochi has a conflict; Boba does not
    owner_with_pet.find_pet("Mochi").add_task(_task("Walk",    "9:00 AM"))
    owner_with_pet.find_pet("Mochi").add_task(_task("Meds",    "9:00 AM"))
    owner_with_pet.find_pet("Boba").add_task(_task("Feeding",  "8:00 AM"))

    sched = Scheduler(owner_with_pet)

    assert len(sched.find_conflicts("Mochi")) == 1
    assert sched.find_conflicts("Boba") == []


def test_multi_pet_build_plan_only_uses_named_pet(owner_with_pet):
    """build_plan() for one pet must not include tasks from other pets."""
    owner_with_pet.add_pet(Pet(name="Boba", species="cat", age=2, breed="Tabby"))
    owner_with_pet.find_pet("Mochi").add_task(_task("Mochi walk",  "9:00 AM"))
    owner_with_pet.find_pet("Boba").add_task(_task("Boba feeding", "9:00 AM"))

    sched = Scheduler(owner_with_pet)
    plan = sched.build_plan("Mochi")

    titles = [s.task.title for s in plan]
    assert "Mochi walk" in titles
    assert "Boba feeding" not in titles
