"""
Tests for PawPal+ Pet Care Management System
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import pawpal_system
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, Schedule, ScheduledTask


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


# ============================================================================
# SORTING CORRECTNESS TESTS
# ============================================================================

def test_sort_tasks_by_priority_and_time():
    """Verify tasks are sorted by priority (high to low) then time (chronological)."""
    owner = Owner(name="Alice", available_minutes=300, preferences={})
    scheduler = Scheduler(owner)

    # Create tasks with varying priorities and times
    tasks = [
        Task(title="Low priority late", category="walk", duration_minutes=30,
             priority=1, due_time="14:00", frequency="once"),
        Task(title="High priority late", category="feeding", duration_minutes=15,
             priority=5, due_time="12:00", frequency="once"),
        Task(title="High priority early", category="medication", duration_minutes=10,
             priority=5, due_time="08:00", frequency="once"),
        Task(title="Medium priority", category="play", duration_minutes=20,
             priority=3, due_time="10:00", frequency="once"),
    ]

    sorted_tasks = scheduler.sort_tasks(tasks)

    # Verify order: priority 5 tasks first (sorted by time), then priority 3, then priority 1
    assert sorted_tasks[0].title == "High priority early"  # priority=5, time=08:00
    assert sorted_tasks[1].title == "High priority late"   # priority=5, time=12:00
    assert sorted_tasks[2].title == "Medium priority"      # priority=3, time=10:00
    assert sorted_tasks[3].title == "Low priority late"    # priority=1, time=14:00


def test_sort_tasks_with_no_due_time():
    """Verify tasks without due_time sort to the end."""
    owner = Owner(name="Alice", available_minutes=300, preferences={})
    scheduler = Scheduler(owner)

    tasks = [
        Task(title="No time", category="walk", duration_minutes=30,
             priority=5, due_time=None, frequency="once"),
        Task(title="Has time", category="feeding", duration_minutes=15,
             priority=5, due_time="08:00", frequency="once"),
        Task(title="Also no time", category="play", duration_minutes=20,
             priority=3, due_time=None, frequency="once"),
    ]

    sorted_tasks = scheduler.sort_tasks(tasks)

    # Task with time should come first (same priority)
    assert sorted_tasks[0].title == "Has time"
    # Tasks without time should be at the end
    assert sorted_tasks[1].title == "No time"
    assert sorted_tasks[2].title == "Also no time"


def test_chronological_order_in_schedule():
    """Verify scheduled tasks appear in chronological order."""
    owner = Owner(name="Bob", available_minutes=200, preferences={})
    pet = Pet(name="Max", species="dog", age_years=5, notes="Good boy")
    owner.add_pet(pet)

    # Add tasks in random order
    pet.add_task(Task(title="Lunch", category="feeding", duration_minutes=10,
                     priority=3, due_time="12:00", frequency="daily"))
    pet.add_task(Task(title="Breakfast", category="feeding", duration_minutes=10,
                     priority=3, due_time="08:00", frequency="daily"))
    pet.add_task(Task(title="Dinner", category="feeding", duration_minutes=10,
                     priority=3, due_time="18:00", frequency="daily"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # Verify chronological order in scheduled tasks
    assert schedule.scheduled_tasks[0].task.title == "Breakfast"  # 08:00
    assert schedule.scheduled_tasks[1].task.title == "Lunch"      # 12:00
    assert schedule.scheduled_tasks[2].task.title == "Dinner"     # 18:00


# ============================================================================
# RECURRENCE LOGIC TESTS
# ============================================================================

def test_complete_daily_task_creates_new_instance():
    """Verify marking a daily task complete creates a new task for the following day."""
    owner = Owner(name="Carol", available_minutes=300, preferences={})
    pet = Pet(name="Luna", species="cat", age_years=2, notes="Playful")
    owner.add_pet(pet)

    # Create a daily task
    daily_task = Task(
        title="Morning feeding",
        category="feeding",
        duration_minutes=15,
        priority=5,
        due_time="08:00",
        frequency="daily"
    )
    pet.add_task(daily_task)

    original_id = daily_task.id
    original_task_count = len(pet.tasks)

    # Complete the task
    scheduler = Scheduler(owner)
    new_task = scheduler.complete_task(pet_name="Luna", task_id=original_id)

    # Verify original task is marked complete
    assert daily_task.completed is True

    # Verify a new task was created
    assert new_task is not None
    assert len(pet.tasks) == original_task_count + 1

    # Verify new task has same attributes but different ID
    assert new_task.title == "Morning feeding"
    assert new_task.category == "feeding"
    assert new_task.duration_minutes == 15
    assert new_task.priority == 5
    assert new_task.due_time == "08:00"
    assert new_task.frequency == "daily"
    assert new_task.completed is False
    assert new_task.id != original_id


def test_complete_weekly_task_creates_new_instance():
    """Verify marking a weekly task complete creates a new task."""
    owner = Owner(name="Dave", available_minutes=300, preferences={})
    pet = Pet(name="Buddy", species="dog", age_years=4, notes="Loves walks")
    owner.add_pet(pet)

    # Create a weekly task
    weekly_task = Task(
        title="Vet checkup",
        category="health",
        duration_minutes=60,
        priority=4,
        due_time="10:00",
        frequency="weekly"
    )
    pet.add_task(weekly_task)

    scheduler = Scheduler(owner)
    new_task = scheduler.complete_task(pet_name="Buddy", task_id=weekly_task.id)

    # Verify new task was created
    assert new_task is not None
    assert new_task.frequency == "weekly"
    assert new_task.completed is False
    assert len(pet.tasks) == 2


def test_complete_once_task_no_new_instance():
    """Verify marking a 'once' task complete does NOT create a new task."""
    owner = Owner(name="Eve", available_minutes=300, preferences={})
    pet = Pet(name="Whiskers", species="cat", age_years=3, notes="Shy")
    owner.add_pet(pet)

    # Create a one-time task
    once_task = Task(
        title="Groom fur",
        category="grooming",
        duration_minutes=45,
        priority=2,
        due_time="14:00",
        frequency="once"
    )
    pet.add_task(once_task)

    scheduler = Scheduler(owner)
    new_task = scheduler.complete_task(pet_name="Whiskers", task_id=once_task.id)

    # Verify NO new task was created
    assert new_task is None
    assert len(pet.tasks) == 1
    assert once_task.completed is True


# ============================================================================
# CONFLICT DETECTION TESTS
# ============================================================================

def test_detect_duplicate_time_conflict():
    """Verify the Scheduler flags duplicate times as conflicts."""
    owner = Owner(name="Frank", available_minutes=300, preferences={})
    pet = Pet(name="Rocky", species="dog", age_years=6, notes="Calm")
    owner.add_pet(pet)

    # Add two tasks with the same due time
    pet.add_task(Task(title="Morning walk", category="exercise", duration_minutes=30,
                     priority=5, due_time="08:00", frequency="daily"))
    pet.add_task(Task(title="Breakfast", category="feeding", duration_minutes=15,
                     priority=5, due_time="08:00", frequency="daily"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # Verify conflict was detected
    assert len(schedule.conflicts) > 0
    assert any("08:00" in conflict for conflict in schedule.conflicts)


def test_detect_overlapping_time_conflict():
    """Verify the Scheduler detects overlapping time ranges."""
    owner = Owner(name="Grace", available_minutes=300, preferences={})
    pet = Pet(name="Bella", species="dog", age_years=2, notes="Energetic")
    owner.add_pet(pet)

    # Task 1: 08:00 - 08:30 (30 minutes)
    pet.add_task(Task(title="Morning walk", category="exercise", duration_minutes=30,
                     priority=5, due_time="08:00", frequency="daily"))
    # Task 2: 08:15 - 08:30 (15 minutes) - overlaps with task 1
    pet.add_task(Task(title="Quick feeding", category="feeding", duration_minutes=15,
                     priority=5, due_time="08:15", frequency="daily"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # Verify overlap conflict was detected
    assert len(schedule.conflicts) > 0
    conflict_text = " ".join(schedule.conflicts)
    assert "overlap" in conflict_text.lower() or "conflict" in conflict_text.lower()


def test_no_conflict_for_non_overlapping_tasks():
    """Verify no conflicts are detected for non-overlapping tasks."""
    owner = Owner(name="Henry", available_minutes=300, preferences={})
    pet = Pet(name="Charlie", species="cat", age_years=5, notes="Sleepy")
    owner.add_pet(pet)

    # Task 1: 08:00 - 08:30
    pet.add_task(Task(title="Morning feeding", category="feeding", duration_minutes=30,
                     priority=5, due_time="08:00", frequency="daily"))
    # Task 2: 09:00 - 09:15 (no overlap)
    pet.add_task(Task(title="Play time", category="play", duration_minutes=15,
                     priority=3, due_time="09:00", frequency="daily"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # Verify no conflicts
    assert len(schedule.conflicts) == 0


def test_conflict_detection_with_multiple_pets():
    """Verify conflicts are detected across different pets (owner can't be in two places)."""
    owner = Owner(name="Iris", available_minutes=400, preferences={})

    pet1 = Pet(name="Dog1", species="dog", age_years=3, notes="Active")
    pet2 = Pet(name="Dog2", species="dog", age_years=4, notes="Lazy")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    # Same time for different pets - owner conflict
    pet1.add_task(Task(title="Walk Dog1", category="exercise", duration_minutes=30,
                      priority=5, due_time="10:00", frequency="daily"))
    pet2.add_task(Task(title="Walk Dog2", category="exercise", duration_minutes=30,
                      priority=5, due_time="10:00", frequency="daily"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # Verify owner conflict was detected
    assert len(schedule.conflicts) > 0


def test_flexible_tasks_no_conflict():
    """Verify flexible tasks (no due_time) don't trigger false conflicts."""
    owner = Owner(name="Jack", available_minutes=300, preferences={})
    pet = Pet(name="Fluffy", species="cat", age_years=1, notes="Kitten")
    owner.add_pet(pet)

    # Multiple flexible tasks should not conflict
    pet.add_task(Task(title="Play 1", category="play", duration_minutes=20,
                     priority=3, due_time=None, frequency="once"))
    pet.add_task(Task(title="Play 2", category="play", duration_minutes=20,
                     priority=3, due_time=None, frequency="once"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # No conflicts should be detected
    assert len(schedule.conflicts) == 0


# ============================================================================
# TASK FILTERING TESTS
# ============================================================================

def test_filter_tasks_by_pet_name():
    """Verify filter_tasks correctly filters by pet name."""
    owner = Owner(name="Kim", available_minutes=300, preferences={})

    pet1 = Pet(name="Spot", species="dog", age_years=3, notes="")
    pet2 = Pet(name="Mittens", species="cat", age_years=2, notes="")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    pet1.add_task(Task(title="Walk Spot", category="exercise", duration_minutes=30,
                      priority=5, due_time="08:00", frequency="daily"))
    pet2.add_task(Task(title="Feed Mittens", category="feeding", duration_minutes=10,
                      priority=5, due_time="08:00", frequency="daily"))

    scheduler = Scheduler(owner)

    # Filter for Spot's tasks
    spot_tasks = scheduler.filter_tasks(pet_name="Spot")
    assert len(spot_tasks) == 1
    assert spot_tasks[0].title == "Walk Spot"

    # Filter for Mittens' tasks
    mittens_tasks = scheduler.filter_tasks(pet_name="Mittens")
    assert len(mittens_tasks) == 1
    assert mittens_tasks[0].title == "Feed Mittens"


def test_filter_tasks_by_completion_status():
    """Verify filter_tasks correctly filters by completion status."""
    owner = Owner(name="Laura", available_minutes=300, preferences={})
    pet = Pet(name="Rex", species="dog", age_years=4, notes="")
    owner.add_pet(pet)

    task1 = Task(title="Completed task", category="walk", duration_minutes=30,
                priority=5, due_time="08:00", frequency="once")
    task1.mark_complete()

    task2 = Task(title="Incomplete task", category="feeding", duration_minutes=15,
                priority=5, due_time="12:00", frequency="once")

    pet.add_task(task1)
    pet.add_task(task2)

    scheduler = Scheduler(owner)

    # Filter for completed tasks only
    completed = scheduler.filter_tasks(completed=True)
    assert len(completed) == 1
    assert completed[0].title == "Completed task"

    # Filter for incomplete tasks only
    incomplete = scheduler.filter_tasks(completed=False)
    assert len(incomplete) == 1
    assert incomplete[0].title == "Incomplete task"

    # Get all tasks (None)
    all_tasks = scheduler.filter_tasks(completed=None)
    assert len(all_tasks) == 2


# ============================================================================
# SCHEDULING WITH TIME CONSTRAINTS TESTS
# ============================================================================

def test_schedule_respects_available_minutes():
    """Verify only tasks that fit within available_minutes are scheduled."""
    owner = Owner(name="Mike", available_minutes=60, preferences={})
    pet = Pet(name="Gizmo", species="cat", age_years=3, notes="")
    owner.add_pet(pet)

    # Add tasks totaling more than 60 minutes
    pet.add_task(Task(title="Task 1", category="play", duration_minutes=30,
                     priority=5, due_time="08:00", frequency="once"))
    pet.add_task(Task(title="Task 2", category="feeding", duration_minutes=20,
                     priority=4, due_time="09:00", frequency="once"))
    pet.add_task(Task(title="Task 3", category="walk", duration_minutes=30,
                     priority=3, due_time="10:00", frequency="once"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # Only first two tasks should fit (30 + 20 = 50 minutes)
    assert len(schedule.scheduled_tasks) == 2
    assert schedule.total_duration == 50
    assert len(schedule.unscheduled_tasks) == 1
    assert schedule.unscheduled_tasks[0][0].title == "Task 3"


def test_total_duration_calculation():
    """Verify total_duration is correctly calculated."""
    owner = Owner(name="Nancy", available_minutes=200, preferences={})
    pet = Pet(name="Sparky", species="dog", age_years=2, notes="")
    owner.add_pet(pet)

    pet.add_task(Task(title="Walk", category="exercise", duration_minutes=45,
                     priority=5, due_time="08:00", frequency="daily"))
    pet.add_task(Task(title="Feed", category="feeding", duration_minutes=15,
                     priority=5, due_time="09:00", frequency="daily"))
    pet.add_task(Task(title="Play", category="play", duration_minutes=30,
                     priority=3, due_time="10:00", frequency="daily"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    # Total should be 45 + 15 + 30 = 90
    assert schedule.total_duration == 90


# ============================================================================
# PET AND TASK CRUD TESTS
# ============================================================================

def test_add_duplicate_pet_raises_error():
    """Verify adding a pet with duplicate name raises ValueError."""
    owner = Owner(name="Oscar", available_minutes=300, preferences={})

    pet1 = Pet(name="Fido", species="dog", age_years=3, notes="")
    owner.add_pet(pet1)

    pet2 = Pet(name="Fido", species="cat", age_years=2, notes="")

    with pytest.raises(ValueError, match="already exists"):
        owner.add_pet(pet2)


def test_remove_nonexistent_pet_raises_error():
    """Verify removing a non-existent pet raises ValueError."""
    owner = Owner(name="Paula", available_minutes=300, preferences={})

    with pytest.raises(ValueError, match="not found"):
        owner.remove_pet("NonexistentPet")


def test_edit_task_updates_attributes():
    """Verify edit_task correctly updates task attributes."""
    pet = Pet(name="Milo", species="cat", age_years=4, notes="")

    task = Task(title="Original title", category="feeding", duration_minutes=15,
               priority=3, due_time="08:00", frequency="once")
    pet.add_task(task)

    # Edit the task
    pet.edit_task(task.id, title="Updated title", priority=5, duration_minutes=20)

    # Verify updates
    assert task.title == "Updated title"
    assert task.priority == 5
    assert task.duration_minutes == 20
    # Unchanged attributes should remain
    assert task.category == "feeding"
    assert task.due_time == "08:00"


def test_remove_nonexistent_task_raises_error():
    """Verify removing a non-existent task raises ValueError."""
    pet = Pet(name="Shadow", species="dog", age_years=5, notes="")

    with pytest.raises(ValueError, match="not found"):
        pet.remove_task("fake-task-id")


def test_list_tasks_respects_include_completed():
    """Verify list_tasks respects the include_completed parameter."""
    pet = Pet(name="Oreo", species="cat", age_years=3, notes="")

    task1 = Task(title="Completed", category="walk", duration_minutes=30,
                priority=5, due_time="08:00", frequency="once")
    task1.mark_complete()

    task2 = Task(title="Incomplete", category="feeding", duration_minutes=15,
                priority=5, due_time="12:00", frequency="once")

    pet.add_task(task1)
    pet.add_task(task2)

    # Include completed
    all_tasks = pet.list_tasks(include_completed=True)
    assert len(all_tasks) == 2

    # Exclude completed
    incomplete_only = pet.list_tasks(include_completed=False)
    assert len(incomplete_only) == 1
    assert incomplete_only[0].title == "Incomplete"


def test_get_all_tasks_aggregates_across_pets():
    """Verify get_all_tasks correctly aggregates tasks from all pets."""
    owner = Owner(name="Quinn", available_minutes=300, preferences={})

    pet1 = Pet(name="Dog", species="dog", age_years=3, notes="")
    pet2 = Pet(name="Cat", species="cat", age_years=2, notes="")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    pet1.add_task(Task(title="Dog task", category="walk", duration_minutes=30,
                      priority=5, due_time="08:00", frequency="once"))
    pet2.add_task(Task(title="Cat task", category="feeding", duration_minutes=15,
                      priority=5, due_time="09:00", frequency="once"))

    all_tasks = owner.get_all_tasks(include_completed=False)

    assert len(all_tasks) == 2
    task_titles = [task.title for task in all_tasks]
    assert "Dog task" in task_titles
    assert "Cat task" in task_titles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
