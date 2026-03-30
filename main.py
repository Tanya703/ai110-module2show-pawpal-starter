from datetime import date, time
from pawpal_system import Owner, Pet, Task, Scheduler


# --- Pets ---
mochi = Pet(name="Mochi", species="dog", age=3, special_needs="joint supplement with dinner")
luna = Pet(name="Luna", species="cat", age=5)

today = date.today()

# --- Tasks added OUT OF ORDER to prove sorting works ---
# frequency + due_date added to recurring tasks
mochi.add_task(Task(title="Evening Walk",    category="walk",       duration_minutes=25, priority="medium", time_of_day_preference="evening",   frequency="daily",  due_date=today))
mochi.add_task(Task(title="Afternoon Play",  category="enrichment", duration_minutes=20, priority="medium", time_of_day_preference="afternoon", frequency="daily",  due_date=today))
mochi.add_task(Task(title="Joint Supplement",category="medication", duration_minutes=5,  priority="high",   time_of_day_preference="morning",   frequency="daily",  due_date=today))
mochi.add_task(Task(title="Morning Walk",    category="walk",       duration_minutes=30, priority="high",   time_of_day_preference="morning",   frequency="daily",  due_date=today))
mochi.add_task(Task(title="Breakfast",       category="feeding",    duration_minutes=10, priority="high",   time_of_day_preference="morning",   frequency="daily",  due_date=today))

# --- Tasks for Luna (also out of order) ---
luna.add_task(Task(title="Wand Toy Play",    category="enrichment", duration_minutes=15, priority="low",    time_of_day_preference="afternoon", frequency="weekly", due_date=today))
luna.add_task(Task(title="Litter Box Clean", category="grooming",   duration_minutes=10, priority="medium", time_of_day_preference="morning",   frequency="daily",  due_date=today))
luna.add_task(Task(title="Breakfast",        category="feeding",    duration_minutes=5,  priority="high",   time_of_day_preference="morning",   frequency="daily",  due_date=today))

# --- CONFLICT DEMO: two tasks pinned to the same start time ---
# Mochi's Vet Check and Luna's Grooming both fixed at 09:00 — should trigger a warning.
mochi.add_task(Task(title="Vet Check",       category="grooming",   duration_minutes=30, priority="high",   time_of_day_preference="morning",   fixed_start_time=time(9, 0)))
luna.add_task( Task(title="Grooming Session",category="grooming",   duration_minutes=20, priority="medium", time_of_day_preference="morning",   fixed_start_time=time(9, 0)))

# Mark one task complete to demo completed filter
mochi.tasks[3].mark_complete()   # Morning Walk → completed

# --- Owner ---
jordan = Owner(
    name="Jordan",
    available_minutes_per_day=150,
    preferred_start_time=time(7, 0),
    preferred_end_time=time(21, 0),
    pets=[mochi, luna],
)

scheduler = Scheduler(owner=jordan)
all_tasks = jordan.get_all_tasks()

# ── Demo 1: sort_by_time ──────────────────────────────────────────────────────
print("=" * 50)
print("  SORTED BY TIME OF DAY (all tasks)")
print("=" * 50)
time_sorted = scheduler.sort_tasks(all_tasks, by="time")
for pet, task in time_sorted:
    slot = task.time_of_day_preference or "anytime"
    done = " [done]" if task.completed else ""
    print(f"  [{slot:<9}] [{task.priority.upper():<6}] {task.title} ({pet.name}){done}")

# ── Demo 2: filter by pet name ────────────────────────────────────────────────
print()
print("=" * 50)
print("  MOCHI'S TASKS ONLY")
print("=" * 50)
mochi_tasks = scheduler.filter_tasks(all_tasks, pet_name="Mochi")
for pet, task in mochi_tasks:
    done = " [done]" if task.completed else ""
    print(f"  {task.title} ({task.priority}){done}")

# ── Demo 3: filter pending only ───────────────────────────────────────────────
print()
print("=" * 50)
print("  PENDING TASKS ONLY (not yet completed)")
print("=" * 50)
pending = scheduler.filter_tasks(all_tasks, completed=False)
for pet, task in pending:
    print(f"  {task.title} ({pet.name})")

# ── Demo 4: filter completed only ────────────────────────────────────────────
print()
print("=" * 50)
print("  COMPLETED TASKS")
print("=" * 50)
done_tasks = scheduler.filter_tasks(all_tasks, completed=True)
for pet, task in done_tasks:
    print(f"  {task.title} ({pet.name})")

# ── Demo 5: recurrence — mark tasks complete, check next occurrence ──────────
print()
print("=" * 50)
print("  RECURRENCE: mark tasks complete")
print("=" * 50)
recur_demos = [
    (mochi, mochi.tasks[2]),   # Joint Supplement — daily
    (luna,  luna.tasks[0]),    # Wand Toy Play    — weekly
]
for pet, task in recur_demos:
    next_task = scheduler.mark_task_complete(pet, task)
    if next_task:
        print(f"  Completed: {task.title} ({pet.name}) | due {task.due_date}")
        print(f"  Next occurrence ({task.frequency}): {next_task.title} due {next_task.due_date}")
    else:
        print(f"  Completed: {task.title} — one-time task, no recurrence.")

# ── Demo 6: full generated schedule with conflict detection ──────────────────
print()
print("=" * 50)
print("       TODAY'S SCHEDULE — PawPal+ (after completions)")
print("=" * 50)
schedule = scheduler.generate_schedule()
for entry in schedule:
    print(f"  {entry['start_time']} – {entry['end_time']}  "
          f"[{entry['priority'].upper():6}]  "
          f"{entry['task']} ({entry['pet']}, {entry['duration_minutes']} min)")

# ── Demo 7: conflict detection ────────────────────────────────────────────────
print()
print("=" * 50)
print("  CONFLICT DETECTION")
print("=" * 50)
conflicts = scheduler.detect_conflicts(schedule)
if conflicts:
    for warning in conflicts:
        print(warning)
else:
    print("  No conflicts detected.")

print("=" * 50)
print()
print(scheduler.explain_choices())
