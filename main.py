"""
PawPal+ Demo Script
Demonstrates the pet care scheduling system
"""

from pawpal_system import Task, Pet, Owner, Scheduler

def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_schedule(schedule) -> None:
    """Print a formatted schedule."""
    print(f"\n📅 Today's Schedule - {schedule.date}")
    print(f"Available time: {schedule.total_duration}/{owner.available_minutes} minutes")
    print("-" * 60)

    if schedule.scheduled_tasks:
        print("\n✓ SCHEDULED TASKS:\n")
        for st in schedule.scheduled_tasks:
            time_display = st.scheduled_time if st.scheduled_time != "flexible" else "Anytime"
            print(f"  {time_display:12} | {st.pet_name:10} | {st.task.title:25}")
            print(f"               | Category: {st.task.category:12} | Duration: {st.task.duration_minutes} min | Priority: {st.task.priority}")
            print()

    if schedule.unscheduled_tasks:
        print("\n⚠️  UNSCHEDULED TASKS (didn't fit in available time):\n")
        for task, pet_name in schedule.unscheduled_tasks:
            print(f"  - {task.title} for {pet_name} ({task.duration_minutes} min, priority {task.priority})")

    if schedule.conflicts:
        print("\n⚠️  SCHEDULING CONFLICTS:\n")
        for conflict in schedule.conflicts:
            print(f"  ! {conflict}")

    print("\n" + "=" * 60)

# Create the owner
print_header("🐾 PawPal+ Pet Care Scheduler")
owner = Owner(
    name="Jordan",
    available_minutes=90,
    preferences={"priority_focus": "health_first"}
)
print(f"\nOwner: {owner.name}")
print(f"Available time today: {owner.available_minutes} minutes")

# Create pets
print_header("Adding Pets")

mochi = Pet(
    name="Mochi",
    species="dog",
    age_years=3,
    notes="High energy, loves outdoor activities"
)
print(f"✓ Added {mochi.name} ({mochi.species}, {mochi.age_years} years old)")

luna = Pet(
    name="Luna",
    species="cat",
    age_years=5,
    notes="Indoor cat, calm temperament"
)
print(f"✓ Added {luna.name} ({luna.species}, {luna.age_years} years old)")

owner.add_pet(mochi)
owner.add_pet(luna)

# Add tasks for Mochi (OUT OF ORDER to test sorting!)
print_header("Adding Tasks for Mochi (Out of Order)")

mochi_tasks = [
    Task(
        title="Playtime in yard",
        category="enrichment",
        duration_minutes=20,
        priority=2,
        due_time=None,  # Flexible time
        frequency="daily"
    ),
    Task(
        title="Medication",
        category="health",
        duration_minutes=5,
        priority=5,
        due_time="09:00",  # Later time
        frequency="daily"
    ),
    Task(
        title="Morning walk",
        category="exercise",
        duration_minutes=30,
        priority=3,
        due_time="08:00",  # Middle time
        frequency="daily"
    ),
    Task(
        title="Breakfast",
        category="feeding",
        duration_minutes=10,
        priority=5,
        due_time="07:30",  # Earliest time
        frequency="daily"
    )
]

for task in mochi_tasks:
    mochi.add_task(task)
    time_str = task.due_time if task.due_time else "flexible"
    print(f"  ✓ {task.title:25} | {time_str:10} | {task.duration_minutes} min | Priority {task.priority}")

# Add tasks for Luna (OUT OF ORDER to test sorting!)
print_header("Adding Tasks for Luna (Out of Order)")

luna_tasks = [
    Task(
        title="Brushing",
        category="grooming",
        duration_minutes=15,
        priority=1,
        due_time=None,  # Flexible
        frequency="weekly"
    ),
    Task(
        title="Litter box cleaning",
        category="hygiene",
        duration_minutes=10,
        priority=3,
        due_time="10:00",  # Later time
        frequency="daily"
    ),
    Task(
        title="Breakfast",
        category="feeding",
        duration_minutes=5,
        priority=4,
        due_time="07:30",  # SAME TIME as Mochi's breakfast - exact conflict!
        frequency="daily"
    ),
    Task(
        title="Playtime",
        category="enrichment",
        duration_minutes=25,
        priority=2,
        due_time="07:50",  # Overlaps with Mochi's 08:00 walk - overlap conflict!
        frequency="daily"
    )
]

for task in luna_tasks:
    luna.add_task(task)
    time_str = task.due_time if task.due_time else "flexible"
    print(f"  ✓ {task.title:25} | {time_str:10} | {task.duration_minutes} min | Priority {task.priority}")

# Test sorting and filtering methods
print_header("Testing Lambda Sorting & Filtering")

scheduler = Scheduler(owner)

# Demo 1: Show tasks sorted by priority + time
print("\n📊 All Mochi's tasks SORTED (by priority, then time):")
sorted_tasks = scheduler.sort_tasks(mochi.tasks)
for task in sorted_tasks:
    time_str = task.due_time if task.due_time else "flexible"
    print(f"  Priority {task.priority} | {time_str:10} | {task.title}")

# Demo 2: Filter incomplete tasks for Mochi
print("\n🔍 Filter: Mochi's incomplete tasks:")
incomplete = scheduler.filter_tasks(pet_name="Mochi", completed=False)
for task in incomplete:
    print(f"  - {task.title}")

# Demo 3: Filter all tasks across all pets
print("\n🔍 Filter: All tasks for all pets:")
all_tasks = scheduler.filter_tasks(pet_name=None, completed=False)
for task in all_tasks:
    time_str = task.due_time if task.due_time else "flexible"
    print(f"  {time_str:10} | {task.title}")

# Demo 4: Test recurring task auto-creation
print_header("Testing Recurring Task Auto-Creation")

# Show Mochi's current tasks
print(f"\n📋 Mochi's tasks BEFORE completion ({len(mochi.tasks)} total):")
for task in mochi.tasks:
    status = "✓" if task.completed else "○"
    print(f"  {status} {task.title} (frequency: {task.frequency}, ID: {task.id[:8]}...)")

# Complete a daily recurring task (Breakfast)
breakfast_task = mochi.tasks[3]  # Breakfast is the 4th task added
print(f"\n🎯 Completing '{breakfast_task.title}' (daily task)...")
new_task = scheduler.complete_task(pet_name="Mochi", task_id=breakfast_task.id)

if new_task:
    print(f"   ✅ Task completed!")
    print(f"   🔄 Auto-created next occurrence: '{new_task.title}' (ID: {new_task.id[:8]}...)")
else:
    print(f"   ✅ Task completed (no auto-creation for 'once' frequency)")

# Show Mochi's tasks after completion
print(f"\n📋 Mochi's tasks AFTER completion ({len(mochi.tasks)} total):")
for task in mochi.tasks:
    status = "✓" if task.completed else "○"
    print(f"  {status} {task.title} (frequency: {task.frequency}, ID: {task.id[:8]}...)")

# Filter to show only incomplete tasks
incomplete_after = scheduler.filter_tasks(pet_name="Mochi", completed=False)
print(f"\n🔍 Mochi's incomplete tasks: {len(incomplete_after)}")
for task in incomplete_after:
    print(f"  - {task.title}")

# Generate and print schedule
print_header("Generating Today's Schedule")

schedule = scheduler.generate_plan(date="2026-02-15")

print_schedule(schedule)

# Show summary statistics
print_header("Summary")
print(f"Total pets: {len(owner.pets)}")
print(f"Total tasks scheduled: {len(schedule.scheduled_tasks)}")
print(f"Total tasks unscheduled: {len(schedule.unscheduled_tasks)}")
print(f"Time utilization: {schedule.total_duration}/{owner.available_minutes} minutes ({int(schedule.total_duration/owner.available_minutes*100)}%)")
print(f"Conflicts detected: {len(schedule.conflicts)}")
print("\n✨ Schedule generation complete!\n")
