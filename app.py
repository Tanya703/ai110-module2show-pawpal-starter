import streamlit as st
from datetime import date, time
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A smart daily planner for pet owners.")

# ---------------------------------------------------------------------------
# Section 1 — Owner & Pet Info
# ---------------------------------------------------------------------------
st.header("1. Owner & Pet Info")

col_a, col_b = st.columns(2)
with col_a:
    owner_name     = st.text_input("Your name", value="Jordan", placeholder="e.g. Jordan")
    available_mins = st.number_input("Available minutes per day", min_value=10, max_value=480, value=120, step=10)
    start_hour     = st.slider("Day starts at (hour)", min_value=5, max_value=12, value=7)
    end_hour       = st.slider("Day ends at (hour)",   min_value=13, max_value=23, value=21)

with col_b:
    pet_name      = st.text_input("Pet's name", value="Mochi", placeholder="e.g. Mochi")
    pet_age       = st.number_input("Pet age (years)", min_value=0, max_value=30, value=3)
    species       = st.selectbox("Species", ["dog", "cat", "other"])
    special_needs = st.text_input("Special needs (optional)", placeholder="e.g. joint supplement with dinner")

st.write("")
if st.button("💾  Save owner & pet", use_container_width=True):
    existing_pet = st.session_state.get("pet")

    # Only create a fresh pet (losing tasks) if the pet name actually changed.
    # Otherwise preserve the existing pet object and just update the owner.
    if existing_pet is None or existing_pet.name != pet_name:
        pet = Pet(
            name=pet_name,
            species=species,
            age=int(pet_age),
            special_needs=special_needs or None,
        )
        st.session_state.pet = pet
        # Clear stale schedule when switching pets
        st.session_state.pop("schedule", None)
    else:
        pet = existing_pet
        pet.species       = species
        pet.age           = int(pet_age)
        pet.special_needs = special_needs or None

    owner = Owner(
        name=owner_name,
        available_minutes_per_day=int(available_mins),
        preferred_start_time=time(start_hour, 0),
        preferred_end_time=time(end_hour, 0),
        pets=[pet],
    )
    st.session_state.owner = owner
    st.success(f"Saved! {owner_name}'s pet {pet_name} ({species}, age {pet_age}).")

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add Tasks
# ---------------------------------------------------------------------------
st.header("2. Add Tasks")

if "pet" not in st.session_state:
    st.info("Save your owner & pet info above before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task title", placeholder="e.g. Morning Walk")
            category   = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
            duration   = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20, step=5)
        with col2:
            priority   = st.selectbox("Priority", ["high", "medium", "low"])
            time_pref  = st.selectbox("Preferred time of day", ["morning", "afternoon", "evening", "none"])
            frequency  = st.selectbox("Repeats", ["none (one-time)", "daily", "weekly"])

        col3, col4 = st.columns(2)
        with col3:
            fixed_hour = st.number_input("Start hour (24h)", min_value=0, max_value=23, value=9)
            fixed_min  = st.number_input("Start minute", min_value=0, max_value=59, value=0, step=15)
        with col4:
            skip_fixed = st.checkbox("No specific start time (let scheduler decide)")

        submitted = st.form_submit_button("➕  Add task", use_container_width=True)

    if submitted:
        if not task_title.strip():
            st.warning("Please enter a task title.")
        else:
            freq_value = None if frequency == "none (one-time)" else frequency
            pref_value = None if time_pref == "none" else time_pref
            fixed_time = None if skip_fixed else time(int(fixed_hour), int(fixed_min))

            task = Task(
                title=task_title.strip(),
                category=category,
                duration_minutes=int(duration),
                priority=priority,
                time_of_day_preference=pref_value,
                frequency=freq_value,
                due_date=date.today() if freq_value else None,
                fixed_start_time=fixed_time,
            )
            st.session_state.pet.add_task(task)
            # Adding a task invalidates any previously generated schedule
            st.session_state.pop("schedule", None)
            st.success(f"Added: {task_title.strip()}")

    # --- Task list ---
    if st.session_state.pet.tasks:
        st.write("")
        total    = len(st.session_state.pet.tasks)
        pending  = sum(1 for t in st.session_state.pet.tasks if not t.completed)
        st.write(f"**{st.session_state.pet.name}'s tasks** — {pending} pending, {total - pending} done")

        scheduler_preview = Scheduler(st.session_state.owner)
        sorted_pairs = scheduler_preview.sort_tasks(
            st.session_state.owner.get_all_tasks(), by="priority"
        )

        for i, (pet, t) in enumerate(sorted_pairs):
            col_info, col_del = st.columns([7, 1])
            with col_info:
                slot  = t.time_of_day_preference or "any time"
                badge = "✅" if t.completed else "⬜"
                fixed = f" @ {t.fixed_start_time.strftime('%H:%M')}" if t.fixed_start_time else ""
                st.write(
                    f"{badge} **{t.title}** — {t.category} | {t.priority} priority | "
                    f"{t.duration_minutes} min | {slot}{fixed}"
                )
            with col_del:
                if st.button("Delete", key=f"del_{i}"):
                    pet.tasks.remove(t)
                    st.session_state.pop("schedule", None)
                    st.experimental_rerun()
    else:
        st.info("No tasks yet — add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Generate Schedule
# ---------------------------------------------------------------------------
st.header("3. Today's Schedule")

if "owner" not in st.session_state:
    st.info("Complete sections 1 and 2 first.")
else:
    pending_tasks = [t for t in st.session_state.pet.tasks if not t.completed]
    if not pending_tasks:
        st.info("No pending tasks — add tasks or mark existing ones incomplete.")
    else:
        if st.button("📅  Generate schedule", use_container_width=True):
            scheduler = Scheduler(st.session_state.owner)
            schedule  = scheduler.generate_schedule()
            conflicts = scheduler.detect_conflicts(schedule)
            st.session_state.schedule  = schedule
            st.session_state.conflicts = conflicts
            st.session_state.scheduler = scheduler

        if "schedule" in st.session_state:
            st.info("Showing last generated schedule. Hit Generate again after any task changes.")

            schedule  = st.session_state.schedule
            conflicts = st.session_state.conflicts
            scheduler = st.session_state.scheduler

            # Conflict warnings
            if conflicts:
                for warning in conflicts:
                    st.warning(warning.strip())
            else:
                st.success("No scheduling conflicts detected.")

            st.write("")

            if schedule:
                sort_by = st.radio("Sort schedule by", ["priority", "time of day"], horizontal=True)
                display = schedule
                if sort_by == "time of day":
                    display = sorted(schedule, key=lambda e: int(e["start_time"].replace(":", "")))

                rows = [
                    {
                        "Time":     f"{e['start_time']} – {e['end_time']}",
                        "Task":     e["task"],
                        "Pet":      e["pet"],
                        "Category": e["category"],
                        "Priority": e["priority"].upper(),
                        "Duration": f"{e['duration_minutes']} min",
                    }
                    for e in display
                ]
                st.dataframe(rows, use_container_width=True)

                # Metrics — recalculate fresh each render to stay accurate
                total_min   = sum(e["duration_minutes"] for e in schedule)
                budget      = st.session_state.owner.available_minutes_per_day
                fresh_pending = [t for t in st.session_state.pet.tasks if not t.completed]
                dropped     = max(0, len(fresh_pending) - len(schedule))

                m1, m2, m3 = st.columns(3)
                m1.metric("Time scheduled", f"{total_min} min")
                m2.metric("Budget remaining", f"{budget - total_min} min")
                m3.metric("Tasks dropped", dropped)

            else:
                st.warning("No tasks fit within your available time budget.")

            with st.expander("Why these tasks?"):
                # Use the stored schedule as the source of truth so this
                # section always matches what was actually generated.
                scheduled_titles = {e["task"] for e in schedule}
                all_tasks        = st.session_state.owner.get_all_tasks()
                pending_all      = scheduler.filter_tasks(all_tasks, completed=False)
                dropped_tasks    = [(pet, task) for pet, task in pending_all
                                    if task.title not in scheduled_titles]

                budget = st.session_state.owner.available_minutes_per_day
                used   = sum(e["duration_minutes"] for e in schedule)

                st.markdown(
                    f"**{st.session_state.owner.name}'s daily budget:** {used} of {budget} minutes used "
                    f"({budget - used} min remaining)"
                )
                st.progress(min(used / budget, 1.0))
                st.write("")

                PRIORITY_COLOR = {"high": "🔴", "medium": "🟡", "low": "🟢"}

                st.markdown("**Included tasks** — sorted high → medium → low priority:")
                for pet, task in sorted(pending_all, key=lambda pt: {"high": 0, "medium": 1, "low": 2}.get(pt[1].priority, 99)):
                    if task.title not in scheduled_titles:
                        continue
                    dot = PRIORITY_COLOR.get(task.priority, "⚪")
                    time_label  = f" · {task.time_of_day_preference}" if task.time_of_day_preference else ""
                    fixed_label = f" · pinned @ {task.fixed_start_time.strftime('%H:%M')}" if task.fixed_start_time else ""
                    recur_label = f" · repeats {task.frequency}" if task.frequency else ""
                    st.markdown(
                        f"- {dot} **{task.title}** ({pet.name}) — "
                        f"{task.duration_minutes} min · {task.priority} priority"
                        f"{time_label}{fixed_label}{recur_label}"
                    )

                if dropped_tasks:
                    st.write("")
                    st.markdown("**Dropped — not enough time remaining:**")
                    for pet, task in dropped_tasks:
                        dot = PRIORITY_COLOR.get(task.priority, "⚪")
                        st.markdown(
                            f"- {dot} ~~{task.title}~~ ({pet.name}) — "
                            f"{task.duration_minutes} min · {task.priority} priority — "
                            f"*would exceed budget*"
                        )
