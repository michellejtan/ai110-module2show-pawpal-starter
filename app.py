import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# Step 2 — Create and save the Owner when the button is clicked
available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=90)

if st.button("Set up owner & pet"):
    pet = Pet(pet_name, species, age=1, breed="Unknown")
    st.session_state.owner = Owner(owner_name, phone="", available_minutes=int(available_minutes))
    st.session_state.owner.add_pet(pet)
    st.success(f"Owner {owner_name} set up with pet {pet_name}!")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

# Step 1 — Initialize the owner slot so it survives reruns
if "owner" not in st.session_state:
    st.session_state.owner = None

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    due_time = st.text_input("Due time", value="9:00 AM")

if st.button("Add task"):
    if st.session_state.owner is not None:
        owner = st.session_state.owner
        pet = owner.find_pet(pet_name)
        if pet:
            pet.add_task(Task(task_title, "general", int(duration), priority, due_time))
            st.success(f"Task '{task_title}' added to {pet_name}.")
        else:
            st.warning(f"No pet named '{pet_name}' found. Set up the owner & pet first.")
    else:
        st.warning("Please set up the owner & pet first.")

if st.session_state.owner is not None:
    pet = st.session_state.owner.find_pet(pet_name)
    if pet and pet.list_tasks():
        st.write("Current tasks:")
        st.table([
            {
                "title": t.title,
                "duration_minutes": t.duration_minutes,
                "priority": t.priority,
                "due_time": t.due_time,
                "completed": t.completed,
            }
            for t in pet.list_tasks()
        ])
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# Step 4 — Debug: show the full session vault to confirm Owner is stored
st.write(st.session_state)

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if st.session_state.owner is not None:
        owner = st.session_state.owner
        pet = owner.find_pet(pet_name)
        if pet and pet.get_pending_tasks():
            scheduler = Scheduler(owner)
            result = scheduler.explain_plan(pet_name)
            st.text(result)
        else:
            st.warning(f"No pending tasks found for {pet_name}. Add tasks first.")
    else:
        st.warning("Please set up the owner & pet first.")
        st.markdown(
        """
Suggested approach:
1. Design your UML (draft).
2. Create class stubs (no logic).
3. Implement scheduling behavior.
4. Connect your scheduler here and display results.
"""
    )
        
