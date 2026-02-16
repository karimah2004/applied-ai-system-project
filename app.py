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

# Show all tasks for current pet
pet = st.session_state.owner.get_pet(st.session_state.current_pet)
if pet and pet.tasks:
    st.write(f"**Tasks for {pet.name}:**")
    task_data = []
    for task in pet.tasks:
        task_data.append({
            "Title": task.title,
            "Category": task.category,
            "Duration": f"{task.duration_minutes} min",
            "Priority": task.priority,
            "Due Time": task.due_time or "flexible",
            "Completed": "✓" if task.completed else ""
        })
    st.table(task_data)

st.divider()

# === SCHEDULE GENERATION ===
st.subheader("4️⃣ Generate Schedule")

# Check if there are any tasks
total_tasks = sum(len(p.tasks) for p in st.session_state.owner.pets)
if total_tasks == 0:
    st.info("Add some tasks first to generate a schedule!")
    st.stop()

st.write(f"📊 Total tasks across all pets: **{total_tasks}**")

if st.button("🗓️ Generate Today's Schedule", type="primary"):
    # Create scheduler and generate plan
    scheduler = Scheduler(st.session_state.owner)
    schedule = scheduler.generate_plan(date="2026-02-15")

    st.success(f"✅ Schedule generated for {schedule.date}")

    # Display scheduled tasks
    if schedule.scheduled_tasks:
        st.subheader("✓ Scheduled Tasks")
        st.write(f"**Total time: {schedule.total_duration}/{st.session_state.owner.available_minutes} minutes** ({int(schedule.total_duration/st.session_state.owner.available_minutes*100)}% utilization)")

        for st_task in schedule.scheduled_tasks:
            time_display = st_task.scheduled_time if st_task.scheduled_time != "flexible" else "Anytime"
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
                with col1:
                    st.write(f"**{time_display}**")
                with col2:
                    st.write(f"{st_task.task.title}")
                with col3:
                    st.write(f"*{st_task.pet_name}* • {st_task.task.category}")
                with col4:
                    st.write(f"{st_task.task.duration_minutes} min")
        st.divider()

    # Display conflicts
    if schedule.conflicts:
        st.subheader("⚠️ Scheduling Conflicts")
        for conflict in schedule.conflicts:
            st.warning(conflict)
        st.divider()

    # Display unscheduled tasks
    if schedule.unscheduled_tasks:
        st.subheader("❌ Unscheduled Tasks (didn't fit in available time)")
        for task, pet_name in schedule.unscheduled_tasks:
            st.write(f"- **{task.title}** for {pet_name} ({task.duration_minutes} min, priority {task.priority})")

    # Summary
    st.divider()
    st.metric("Tasks Scheduled", len(schedule.scheduled_tasks))
    st.metric("Tasks Unscheduled", len(schedule.unscheduled_tasks))
    st.metric("Conflicts Detected", len(schedule.conflicts))
