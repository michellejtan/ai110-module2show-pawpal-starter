import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_COLORS = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

def priority_label(p: str) -> str:
    return PRIORITY_COLORS.get(p.lower(), p)

st.title("🐾 PawPal+")
st.caption("Your daily pet care planner")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1 — Owner & Pet Setup
# ---------------------------------------------------------------------------
st.subheader("Set Up Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input(
        "Available minutes today", min_value=10, max_value=480, value=90
    )
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Set up owner & pet", type="primary"):
    pet = Pet(pet_name, species, age=1, breed="Unknown")
    st.session_state.owner = Owner(owner_name, phone="", available_minutes=int(available_minutes))
    st.session_state.owner.add_pet(pet)
    st.success(f"Owner **{owner_name}** set up with pet **{pet_name}** ({int(available_minutes)} min available today).")

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a Task
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    due_time = st.text_input("Due time", value="9:00 AM",
                              help='Use format like "9:00 AM" or "2:30 PM"')
with col5:
    frequency_choice = st.selectbox("Frequency", ["one-time", "daily", "weekly"])
    frequency = None if frequency_choice == "one-time" else frequency_choice

if st.button("Add task"):
    if st.session_state.owner is None:
        st.warning("Please set up the owner & pet first.")
    else:
        owner = st.session_state.owner
        pet = owner.find_pet(pet_name)
        if pet is None:
            st.warning(f"No pet named '{pet_name}' found. Set up the owner & pet first.")
        else:
            pet.add_task(Task(task_title, "general", int(duration), priority, due_time, frequency=frequency))
            st.success(f"Task **'{task_title}'** added to {pet_name}.")

            # Conflict check immediately after adding
            scheduler = Scheduler(owner)
            conflicts = scheduler.find_conflicts(pet_name)
            for a, b in conflicts:
                st.warning(
                    f"**Scheduling conflict detected for {pet_name}:** "
                    f"'**{a.title}**' and '**{b.title}**' are both due at **{a.due_time}**. "
                    f"Please change one task's due time."
                )

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Task List (sorted + filtered)
# ---------------------------------------------------------------------------
st.subheader("Current Tasks")

if st.session_state.owner is None:
    st.info("No tasks yet. Set up an owner & pet, then add tasks above.")
else:
    owner = st.session_state.owner
    scheduler = Scheduler(owner)
    pet = owner.find_pet(pet_name)

    # Filter controls
    filter_col, sort_col = st.columns([2, 1])
    with filter_col:
        filter_choice = st.radio(
            "Show tasks",
            ["All", "Pending only", "Completed only"],
            horizontal=True,
        )
    with sort_col:
        st.markdown("&nbsp;", unsafe_allow_html=True)  # vertical spacer

    # Determine completed filter argument
    completed_filter = None
    if filter_choice == "Pending only":
        completed_filter = False
    elif filter_choice == "Completed only":
        completed_filter = True

    # Use Scheduler.filter_tasks() then sort_by_time()
    filtered = scheduler.filter_tasks(completed=completed_filter, pet_name=pet_name)
    sorted_tasks = scheduler.sort_by_time(filtered)

    if not sorted_tasks:
        st.info("No tasks match the selected filter.")
    else:
        # Collect conflict titles for visual annotation
        conflict_pairs = scheduler.find_conflicts(pet_name)
        conflict_titles = {t.title for pair in conflict_pairs for t in pair}

        rows = []
        for t in sorted_tasks:
            title_display = f"⚠ {t.title}" if t.title in conflict_titles else t.title
            rows.append({
                "Title": title_display,
                "Due Time": t.due_time,
                "Priority": priority_label(t.priority),
                "Duration (min)": t.duration_minutes,
                "Frequency": t.frequency if t.frequency else "one-time",
                "Completed": "✓" if t.completed else "",
            })
        st.table(rows)

        # Show conflict banner if any exist
        if conflict_pairs:
            for a, b in conflict_pairs:
                st.warning(
                    f"**Conflict:** '**{a.title}**' and '**{b.title}**' "
                    f"are both due at **{a.due_time}**. "
                    f"Change one task's due time before generating a schedule."
                )

    # Mark task complete
    if pet and pet.list_tasks():
        st.markdown("**Mark a task complete:**")
        pending_titles = [t.title for t in (pet.get_pending_tasks() or [])]
        if pending_titles:
            mark_col1, mark_col2 = st.columns([3, 1])
            with mark_col1:
                task_to_complete = st.selectbox("Select task", pending_titles, label_visibility="collapsed")
            with mark_col2:
                if st.button("Mark done"):
                    scheduler.mark_task_complete(pet_name, task_to_complete)
                    st.success(f"'{task_to_complete}' marked as complete.")
                    st.rerun()
        else:
            st.info("All tasks are already completed.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate Schedule
# ---------------------------------------------------------------------------
st.subheader("Generate Schedule")

start_time_input = st.text_input(
    "Owner available from",
    value="8:00 AM",
    help='Earliest start time for the schedule, e.g. "8:00 AM"'
)

if st.button("Generate schedule", type="primary"):
    if st.session_state.owner is None:
        st.warning("Please set up the owner & pet first.")
    else:
        owner = st.session_state.owner
        pet = owner.find_pet(pet_name)
        scheduler = Scheduler(owner)

        if pet is None or not pet.get_pending_tasks():
            st.warning(f"No pending tasks found for {pet_name}. Add tasks first.")
        else:
            # Show conflict warning before building the plan
            conflict_summary = scheduler.conflict_summary(pet_name)
            if conflict_summary:
                st.warning(
                    "**Scheduling conflicts detected — your plan may be incomplete.** "
                    "Resolve these before relying on the schedule:\n\n" + conflict_summary
                )

            plan = scheduler.build_plan(pet_name, start_time=start_time_input)

            if not plan:
                st.info("Nothing could be scheduled.")
            else:
                st.success(
                    f"Daily plan for **{pet_name}** — "
                    f"{owner.available_minutes} min available, starting {start_time_input}"
                )

                scheduled_rows = []
                skipped_rows = []
                for s in plan:
                    row = {
                        "Time": s.start_time if s.start_time else "SKIPPED",
                        "Task": s.task.title,
                        "Priority": priority_label(s.task.priority),
                        "Duration (min)": s.task.duration_minutes,
                        "Note": s.reason,
                    }
                    if s.start_time:
                        scheduled_rows.append(row)
                    else:
                        skipped_rows.append(row)

                if scheduled_rows:
                    st.markdown("**Scheduled tasks:**")
                    st.table(scheduled_rows)

                if skipped_rows:
                    st.markdown("**Skipped tasks:**")
                    st.table(skipped_rows)
