"""
Tests for PawPal+ Pet Care Management System
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import pawpal_system
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    """Verify that calling mark_complete() actually changes the task's status."""
    # Create a task (starts as incomplete by default)
    task = Task(
        title="Morning walk",
        category="exercise",
        duration_minutes=30,
        priority=3,
        due_time="08:00",
        frequency="daily"
    )

    # Verify initial state
    assert task.completed is False

    # Mark as complete
    task.mark_complete()

    # Verify status changed
    assert task.completed is True


def test_adding_task_increases_count():
    """Verify that adding a task to a Pet increases that pet's task count."""
    # Create a pet with no tasks
    pet = Pet(
        name="Mochi",
        species="dog",
        age_years=3,
        notes="Energetic"
    )

    # Verify initial task count
    assert len(pet.tasks) == 0

    # Create and add a task
    task = Task(
        title="Morning walk",
        category="exercise",
        duration_minutes=30,
        priority=3,
        due_time="08:00",
        frequency="daily"
    )
    pet.add_task(task)

    # Verify count increased
    assert len(pet.tasks) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
