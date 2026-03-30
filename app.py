import streamlit as st
from datetime import time
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Owner & Pet setup ---
st.subheader("Owner & Pet Info")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes per day", min_value=10, max_value=480, value=120)
pet_name = st.text_input("Pet name", value="Mochi")
pet_age = st.number_input("Pet age", min_value=0, max_value=30, value=1)
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save owner & pet"):
    pet = Pet(name=pet_name, species=species, age=int(pet_age))
    owner = Owner(
        name=owner_name,
        available_minutes_per_day=int(available_minutes),
        preferred_start_time=time(7, 0),
        preferred_end_time=time(21, 0),
    )
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.tasks = []
    st.success(f"Saved! {owner_name} with pet {pet_name}.")

st.divider()

# --- Task addition ---
st.subheader("Tasks")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
with col4:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    if "pet" not in st.session_state:
        st.warning("Save your owner & pet info first.")
    else:
        task = Task(
            title=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=priority,
        )
        st.session_state.pet.add_task(task)
        st.success(f"Added task: {task_title}")

if "pet" in st.session_state and st.session_state.pet.tasks:
    st.write("Current tasks:")
    st.table([t.to_dict() for t in st.session_state.pet.tasks])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule generation ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if "owner" not in st.session_state:
        st.warning("Save your owner & pet info first.")
    elif not st.session_state.pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        schedule = scheduler.generate_schedule()
        explanation = scheduler.explain_choices()

        if schedule:
            st.success("Schedule generated!")
            st.table(schedule)
        else:
            st.warning("No tasks fit within the available time budget.")

        st.markdown("### Explanation")
        st.text(explanation)
