import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, Schedule, ScheduledTask

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
**PawPal+** is a pet care planning assistant. It helps you plan care tasks
for your pet(s) based on constraints like time, priority, and preferences.
"""
)

# Initialize session state
if "owner" not in st.session_state:
    st.session_state.owner = None
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None

st.divider()

# === OWNER SETUP ===
st.subheader("1️⃣ Owner Profile")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_time = st.number_input(
        "Available time today (minutes)",
        min_value=30,
        max_value=480,
        value=120
    )

if st.button("Create/Update Owner"):
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=available_time,
        preferences={"priority_focus": "health_first"}
    )
    st.success(f"✓ Owner '{owner_name}' created with {available_time} minutes available!")

# Show current owner
if st.session_state.owner:
    st.info(f"👤 Current owner: **{st.session_state.owner.name}** | {st.session_state.owner.available_minutes} min available | {len(st.session_state.owner.pets)} pet(s)")
else:
    st.warning("⚠️ Create an owner profile to continue")
    st.stop()

st.divider()

# === PET MANAGEMENT ===
st.subheader("2️⃣ Add Pets")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
with col3:
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

pet_notes = st.text_input("Notes", value="Energetic and friendly")

if st.button("Add Pet"):
    try:
        new_pet = Pet(
            name=pet_name,
            species=species,
            age_years=age,
            notes=pet_notes
        )
        st.session_state.owner.add_pet(new_pet)
        st.session_state.current_pet = pet_name
        st.success(f"✓ Added {pet_name} the {species}!")
    except ValueError as e:
        st.error(f"Error: {e}")

# Display existing pets
if st.session_state.owner.pets:
    st.write("**Your Pets:**")
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet = st.selectbox("Select pet to add tasks", pet_names)
    st.session_state.current_pet = selected_pet

    # Show selected pet details
    pet = st.session_state.owner.get_pet(selected_pet)
    st.caption(f"{pet.species.capitalize()}, {pet.age_years} years old - {pet.notes}")
else:
    st.info("No pets yet. Add your first pet above!")
    st.stop()

st.divider()

# === TASK MANAGEMENT ===
st.subheader("3️⃣ Add Tasks")

col1, col2 = st.columns(2)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
    task_category = st.selectbox(
        "Category",
        ["exercise", "feeding", "health", "grooming", "enrichment", "hygiene"]
    )
    task_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

with col2:
    task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    task_priority = st.slider("Priority (1=low, 5=high)", min_value=1, max_value=5, value=3)
    task_time = st.text_input("Due time (HH:MM, or leave empty)", value="", placeholder="08:00")

if st.button("Add Task"):
    pet = st.session_state.owner.get_pet(st.session_state.current_pet)
    if pet:
        new_task = Task(
            title=task_title,
            category=task_category,
            duration_minutes=task_duration,
            priority=task_priority,
            due_time=task_time if task_time else None,
            frequency=task_frequency
        )
        pet.add_task(new_task)
        st.success(f"✓ Added '{task_title}' to {pet.name}'s tasks!")

# Show all tasks with sorting and filtering
pet = st.session_state.owner.get_pet(st.session_state.current_pet)
if pet and pet.tasks:
    # Create an expander for better organization
    with st.expander(f"📋 **{pet.name}'s Task List** ({len(pet.tasks)} total tasks)", expanded=True):

        # Add sorting and filtering controls
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_enabled = st.checkbox("🔄 Sort by priority & time", value=True)
        with col2:
            filter_completed = st.selectbox(
                "🔍 Filter:",
                ["All tasks", "Only incomplete", "Only completed"]
            )
        with col3:
            if st.button("✅ Mark all complete", use_container_width=True):
                for task in pet.tasks:
                    task.completed = True
                st.success(f"All tasks for {pet.name} marked complete!")
                st.rerun()

        st.divider()

        # Create a scheduler to use its methods
        scheduler = Scheduler(st.session_state.owner)

        # Apply filtering
        if filter_completed == "Only incomplete":
            filtered_tasks = scheduler.filter_tasks(pet_name=pet.name, completed=False)
        elif filter_completed == "Only completed":
            filtered_tasks = scheduler.filter_tasks(pet_name=pet.name, completed=True)
        else:
            filtered_tasks = scheduler.filter_tasks(pet_name=pet.name, completed=None)

        # Apply sorting
        if sort_enabled:
            display_tasks = scheduler.sort_tasks(filtered_tasks)
        else:
            display_tasks = filtered_tasks

        # Display tasks with professional formatting
        if display_tasks:
            # Show filter results
            if len(display_tasks) != len(pet.tasks):
                st.info(f"📊 Showing **{len(display_tasks)}** of **{len(pet.tasks)}** tasks")

            # Create DataFrame for better display
            task_data = []
            for task in display_tasks:
                task_data.append({
                    "Status": "✅" if task.completed else "⏳",
                    "Task": task.title,
                    "Category": task.category.capitalize(),
                    "Priority": "⭐" * task.priority,
                    "Duration": f"{task.duration_minutes} min",
                    "Due Time": task.due_time or "Flexible",
                    "Frequency": task.frequency.capitalize()
                })

            # Display as interactive dataframe
            st.dataframe(
                task_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Task": st.column_config.TextColumn("Task", width="medium"),
                    "Priority": st.column_config.TextColumn("Priority", width="small"),
                }
            )

            # Show quick stats
            completed_count = sum(1 for t in display_tasks if t.completed)
            total_time = sum(t.duration_minutes for t in display_tasks)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Completed", f"{completed_count}/{len(display_tasks)}")
            with col2:
                st.metric("Total Time", f"{total_time} min")
            with col3:
                avg_priority = sum(t.priority for t in display_tasks) / len(display_tasks)
                st.metric("Avg Priority", f"{avg_priority:.1f}/5")

        else:
            st.warning(f"⚠️ No tasks match the filter: **{filter_completed}**")

st.divider()

# === VIEW ALL TASKS (FILTERING DEMO) ===
st.subheader("🔍 Task Overview (All Pets)")

# Check if there are any tasks
total_tasks = sum(len(p.tasks) for p in st.session_state.owner.pets)
if total_tasks == 0:
    st.info("Add some tasks first to view the overview!")
else:
    scheduler = Scheduler(st.session_state.owner)

    col1, col2 = st.columns(2)
    with col1:
        view_pet = st.selectbox(
            "Filter by pet:",
            ["All pets"] + [p.name for p in st.session_state.owner.pets]
        )
    with col2:
        view_status = st.selectbox(
            "Filter by status:",
            ["All statuses", "Incomplete only", "Completed only"],
            key="overview_filter"
        )

    # Apply filters
    pet_filter = None if view_pet == "All pets" else view_pet

    if view_status == "Incomplete only":
        status_filter = False
    elif view_status == "Completed only":
        status_filter = True
    else:
        status_filter = None

    filtered_overview = scheduler.filter_tasks(pet_name=pet_filter, completed=status_filter)
    sorted_overview = scheduler.sort_tasks(filtered_overview)

    # Display filtered tasks
    if sorted_overview:
        st.write(f"**Showing {len(sorted_overview)} task(s)** (sorted by priority & time)")
        for idx, task in enumerate(sorted_overview):
            # Find which pet owns this task
            task_pet = next((p.name for p in st.session_state.owner.pets if task in p.tasks), "Unknown")

            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                with col1:
                    status_icon = "✅" if task.completed else "⏳"
                    st.write(f"{status_icon} **{task.title}**")
                with col2:
                    st.write(f"🐾 {task_pet}")
                with col3:
                    st.write(f"{'⭐' * task.priority} {task.category}")
                with col4:
                    st.write(f"⏰ {task.due_time or 'flexible'}")
                with col5:
                    if st.button("✓" if not task.completed else "↺", key=f"toggle_{idx}"):
                        task.completed = not task.completed
                        st.rerun()
    else:
        st.info("No tasks match the current filters.")

st.divider()

# === SCHEDULE GENERATION ===
st.subheader("4️⃣ Generate Schedule")

st.write(f"📊 Total tasks across all pets: **{total_tasks}**")

if total_tasks == 0:
    st.info("Add some tasks first to generate a schedule!")
    st.stop()

col1, col2 = st.columns([3, 1])
with col1:
    schedule_button = st.button("🗓️ Generate Today's Schedule", type="primary", use_container_width=True)
with col2:
    show_all_tasks = st.checkbox("Show all pets", value=True)

if schedule_button:
    # Create scheduler and generate plan
    scheduler = Scheduler(st.session_state.owner)
    schedule = scheduler.generate_plan(date="2026-02-15")

    st.success(f"✅ Schedule generated for {schedule.date}")

    # Alert about conflicts upfront if they exist
    if schedule.conflicts:
        st.error(f"🚨 {len(schedule.conflicts)} conflict(s) detected! Review warnings below.")

    # Display scheduled tasks
    if schedule.scheduled_tasks:
        st.subheader("📅 Scheduled Tasks")

        # Utilization metrics
        utilization = int(schedule.total_duration/st.session_state.owner.available_minutes*100)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Duration", f"{schedule.total_duration} min")
        with col2:
            st.metric("Available Time", f"{st.session_state.owner.available_minutes} min")
        with col3:
            color = "🟢" if utilization < 80 else "🟡" if utilization < 100 else "🔴"
            st.metric("Utilization", f"{color} {utilization}%")

        st.write("")  # spacing

        # Display tasks in timeline format
        for st_task in schedule.scheduled_tasks:
            time_display = st_task.scheduled_time if st_task.scheduled_time != "flexible" else "⏰ Flexible"
            priority_stars = "⭐" * st_task.task.priority

            # Check if this task is involved in a conflict
            has_conflict = any(st_task.task.title in conflict for conflict in schedule.conflicts)
            border_color = "red" if has_conflict else "blue"

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
                with col1:
                    st.write(f"**{time_display}**")
                    if has_conflict:
                        st.caption("⚠️ Conflict!")
                with col2:
                    st.write(f"**{st_task.task.title}**")
                    st.caption(f"{priority_stars} Priority {st_task.task.priority}")
                with col3:
                    st.write(f"🐾 *{st_task.pet_name}*")
                    st.caption(f"📂 {st_task.task.category}")
                with col4:
                    st.write(f"⏱️ {st_task.task.duration_minutes} min")

        st.divider()

    # Display conflicts with enhanced formatting
    if schedule.conflicts:
        st.subheader("⚠️ Scheduling Conflicts Detected")
        st.caption("These tasks overlap in time. Consider adjusting schedules or priorities.")
        for i, conflict in enumerate(schedule.conflicts, 1):
            st.error(f"**Conflict {i}:** {conflict}")
        st.divider()

    # Display unscheduled tasks
    if schedule.unscheduled_tasks:
        st.subheader("❌ Unscheduled Tasks")
        st.caption("These tasks didn't fit within your available time. Consider extending available time or lowering priority.")
        for task, pet_name in schedule.unscheduled_tasks:
            st.warning(f"**{task.title}** for {pet_name} • {task.duration_minutes} min • Priority: {'⭐' * task.priority}")

    # Summary dashboard
    st.divider()
    st.subheader("📊 Schedule Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Tasks Scheduled", len(schedule.scheduled_tasks))
    with col2:
        st.metric("❌ Tasks Unscheduled", len(schedule.unscheduled_tasks))
    with col3:
        conflict_status = "🚨" if schedule.conflicts else "✓"
        st.metric("⚠️ Conflicts", f"{conflict_status} {len(schedule.conflicts)}")
