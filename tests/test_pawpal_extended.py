import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def test_reset_recurring_task():
    """Task.reset() should set completed back to False for a recurring task."""
    task = Task(
        title="Morning feeding",
        task_type="feeding",
        duration_minutes=10,
        priority="high",
        due_time="8:00 AM",
        completed=True,
        frequency="daily",
    )
    task.reset()
    assert task.completed is False


def test_reset_non_recurring_task():
    """Task.reset() should do nothing when frequency is None (one-time task)."""
    task = Task(
        title="Vet appointment",
        task_type="vet",
        duration_minutes=60,
        priority="high",
        due_time="10:00 AM",
        completed=True,
    )
    task.reset()
    assert task.completed is True


def test_priority_value_known_priorities():
    """Task.priority_value() should return 3, 2, 1 for high, medium, low."""
    assert Task("a", "walk", 10, "high", "9:00 AM").priority_value() == 3
    assert Task("b", "walk", 10, "medium", "9:00 AM").priority_value() == 2
    assert Task("c", "walk", 10, "low", "9:00 AM").priority_value() == 1


def test_priority_value_unknown_priority():
    """Task.priority_value() should return 0 for an unrecognised priority string."""
    task = Task("a", "walk", 10, "urgent", "9:00 AM")
    assert task.priority_value() == 0


def test_remove_task_removes_correct_task():
    """Pet.remove_task() should remove only the task matching the given title."""
    pet = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    task1 = Task("Morning walk", "walk", 20, "high", "9:00 AM")
    task2 = Task("Give medication", "medication", 5, "high", "8:00 AM")
    pet.add_task(task1)
    pet.add_task(task2)
    pet.remove_task("Morning walk")
    titles = [t.title for t in pet.tasks]
    assert "Morning walk" not in titles
    assert "Give medication" in titles


def test_get_pending_tasks_excludes_completed():
    """Pet.get_pending_tasks() should return only tasks where completed is False."""
    pet = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    done = Task("Morning walk", "walk", 20, "high", "9:00 AM", completed=True)
    pending = Task("Give medication", "medication", 5, "high", "8:00 AM", completed=False)
    pet.add_task(done)
    pet.add_task(pending)
    result = pet.get_pending_tasks()
    assert len(result) == 1
    assert result[0].title == "Give medication"
