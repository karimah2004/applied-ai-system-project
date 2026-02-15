"""
PawPal+ Pet Care Management System
Class skeleton based on UML design
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """Represents a pet care task with scheduling and completion tracking."""

    id: str
    title: str
    category: str
    duration_minutes: int
    priority: int
    due_time: Optional[str]
    frequency: str
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        pass

    def mark_incomplete(self) -> None:
        """Mark the task as incomplete."""
        pass

    def time_key(self) -> str:
        """Return a sortable time key for the task."""
        pass


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
        pass

    def edit_task(self, task_id: str, **updates) -> None:
        """Edit an existing task by ID with the provided updates."""
        pass

    def remove_task(self, task_id: str) -> None:
        """Remove a task by ID."""
        pass

    def list_tasks(self, include_completed: bool = True) -> list[Task]:
        """List all tasks, optionally filtering out completed ones."""
        pass


class Owner:
    """Represents a pet owner who manages multiple pets."""

    def __init__(self, name: str, available_minutes: int, preferences: dict):
        """Initialize an owner with name, available time, and preferences."""
        self.name: str = name
        self.available_minutes: int = available_minutes
        self.preferences: dict = preferences
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's pet list."""
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        pass

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Get a pet by name."""
        pass

    def get_all_tasks(self, include_completed: bool = False) -> list[Task]:
        """Get all tasks across all pets."""
        pass


class Scheduler:
    """Generates and manages daily task schedules for a pet owner."""

    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner."""
        self.owner: Owner = owner

    def generate_plan(self, date: str = "today") -> list[Task]:
        """Generate a daily task plan for the given date."""
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority and time."""
        pass

    def filter_tasks(self, pet_name: Optional[str] = None,
                    completed: Optional[bool] = None) -> list[Task]:
        """Filter tasks by pet name and/or completion status."""
        pass

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Detect scheduling conflicts in the task list."""
        pass
