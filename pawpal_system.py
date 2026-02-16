"""
PawPal+ Pet Care Management System
Class skeleton based on UML design
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Task:
    """Represents a pet care task with scheduling and completion tracking.

    Attributes:
        id: Unique identifier (auto-generated UUID if not provided)
        title: Task name/description
        category: Task category (e.g., "walk", "feeding", "medication")
        duration_minutes: Estimated time to complete task
        priority: Task priority (higher number = higher priority)
        due_time: Preferred time for task in "HH:MM" format (24-hour), or None
        “frequency: Recurrence rule (e.g., 'once', 'daily', 'weekly') used by the scheduler”
        completed: Whether the task has been completed
    """

    title: str
    category: str
    duration_minutes: int
    priority: int
    due_time: Optional[str]
    frequency: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark the task as incomplete."""
        self.completed = False

    def time_key(self) -> str:
        """Return a sortable time key for the task.

        Returns due_time if set, otherwise returns "99:99" to sort to end.
        """
        return self.due_time if self.due_time else "99:99"


@dataclass
class ScheduledTask:
    """Represents a task scheduled for a specific time with pet context.

    Attributes:
        task: The task to be performed
        scheduled_time: When the task is scheduled (e.g., "08:00")
        pet_name: Name of the pet this task is for
    """

    task: Task
    scheduled_time: str
    pet_name: str


@dataclass
class Schedule:
    """Represents a daily schedule with tasks and their scheduled times.

    Attributes:
        date: The date this schedule is for (e.g., "2026-02-15" or "today")
        scheduled_tasks: List of scheduled tasks with time and pet context
        total_duration: Total minutes of scheduled tasks
        conflicts: List of conflict warning messages (e.g., overlapping times)
        unscheduled_tasks: List of (task, pet_name) that couldn't fit in available time
    """

    date: str
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    total_duration: int = 0
    conflicts: list[str] = field(default_factory=list)
    unscheduled_tasks: list[tuple[Task, str]] = field(default_factory=list)


@dataclass
class Pet:
    """Represents a pet with associated tasks."""

    name: str
    species: str
    age_years: int
    notes: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the pet's task list."""
        self.tasks.append(task)

    def edit_task(self, task_id: str, **updates) -> None:
        """Edit an existing task by ID with the provided updates."""
        for task in self.tasks:
            if task.id == task_id:
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                return
        raise ValueError(f"Task with ID {task_id} not found")

    def remove_task(self, task_id: str) -> None:
        """Remove a task by ID."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                return
        raise ValueError(f"Task with ID {task_id} not found")

    def list_tasks(self, include_completed: bool = True) -> list[Task]:
        """List all tasks, optionally filtering out completed ones."""
        if include_completed:
            return self.tasks.copy()
        return [task for task in self.tasks if not task.completed]


class Owner:
    """Represents a pet owner who manages multiple pets."""

    def __init__(self, name: str, available_minutes: int, preferences: dict):
        """Initialize an owner with name, available time, and preferences."""
        self.name: str = name
        self.available_minutes: int = available_minutes
        self.preferences: dict = preferences
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's pet list.

        Note: Pet names should be unique per owner to ensure get_pet() and
        remove_pet() work correctly. Implementation should validate uniqueness.
        """
        # Check for duplicate names
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"Pet with name '{pet.name}' already exists")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        for i, pet in enumerate(self.pets):
            if pet.name == pet_name:
                self.pets.pop(i)
                return
        raise ValueError(f"Pet with name '{pet_name}' not found")

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Get a pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self, include_completed: bool = False) -> list[Task]:
        """Get all tasks across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.list_tasks(include_completed=include_completed))
        return all_tasks


class Scheduler:
    """Generates and manages daily task schedules for a pet owner."""

    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner."""
        self.owner: Owner = owner

    def generate_plan(self, date: str = "today") -> Schedule:
        """Generate a daily task plan for the given date.

        Returns a Schedule object containing scheduled tasks with times,
        any conflicts detected, and tasks that couldn't be scheduled.
        """
        # Get all incomplete tasks with pet context
        tasks_with_pets = []
        for pet in self.owner.pets:
            for task in pet.list_tasks(include_completed=False):
                tasks_with_pets.append((task, pet.name))

        # Sort tasks by priority and time
        tasks_with_pets.sort(key=lambda tp: (-tp[0].priority, tp[0].time_key()))

        # Schedule tasks within available time
        scheduled_tasks = []
        unscheduled_tasks = []
        total_duration = 0

        for task, pet_name in tasks_with_pets:
            if total_duration + task.duration_minutes <= self.owner.available_minutes:
                # Determine scheduled time
                scheduled_time = task.due_time if task.due_time else "flexible"

                scheduled_task = ScheduledTask(
                    task=task,
                    scheduled_time=scheduled_time,
                    pet_name=pet_name
                )
                scheduled_tasks.append(scheduled_task)
                total_duration += task.duration_minutes
            else:
                unscheduled_tasks.append((task, pet_name))

        # Detect conflicts in scheduled tasks
        scheduled_task_objects = [st.task for st in scheduled_tasks]
        conflicts = self.detect_conflicts(scheduled_task_objects)

        return Schedule(
            date=date,
            scheduled_tasks=scheduled_tasks,
            total_duration=total_duration,
            conflicts=conflicts,
            unscheduled_tasks=unscheduled_tasks
        )

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority and time."""
        # Sort by priority (descending) then by time (ascending)
        return sorted(tasks, key=lambda t: (-t.priority, t.time_key()))

    def filter_tasks(self, pet_name: Optional[str] = None,
                    completed: Optional[bool] = None) -> list[Task]:
        """Filter tasks by pet name and/or completion status.

        Args:
            pet_name: If provided, only return tasks from pet with this name
            completed: If True, only completed tasks; if False, only incomplete; if None, all tasks

        Returns:
            Filtered list of tasks. Traverses owner.pets to gather tasks.
        """
        filtered_tasks = []

        # Determine which pets to check
        pets_to_check = self.owner.pets
        if pet_name:
            pet = self.owner.get_pet(pet_name)
            pets_to_check = [pet] if pet else []

        # Gather tasks from selected pets
        for pet in pets_to_check:
            for task in pet.tasks:
                # Filter by completion status if specified
                if completed is None:
                    filtered_tasks.append(task)
                elif completed and task.completed:
                    filtered_tasks.append(task)
                elif not completed and not task.completed:
                    filtered_tasks.append(task)

        return filtered_tasks

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Detect scheduling conflicts in the task list."""
        conflicts = []

        # Check for time overlaps
        for i, task1 in enumerate(tasks):
            if not task1.due_time:
                continue

            for task2 in tasks[i + 1:]:
                if not task2.due_time:
                    continue

                # Simple conflict: same due_time
                if task1.due_time == task2.due_time:
                    conflicts.append(
                        f"Time conflict: '{task1.title}' and '{task2.title}' "
                        f"both scheduled at {task1.due_time}"
                    )

        return conflicts
