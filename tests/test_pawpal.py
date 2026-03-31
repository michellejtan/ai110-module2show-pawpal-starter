import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


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
