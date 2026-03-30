from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler


# --- Pets ---
mochi = Pet(name="Mochi", species="dog", age=3, special_needs="joint supplement with dinner")
luna = Pet(name="Luna", species="cat", age=5)

# --- Tasks for Mochi ---
mochi.add_task(Task(title="Morning Walk",    category="walk",        duration_minutes=30, priority="high",   time_of_day_preference="morning"))
mochi.add_task(Task(title="Breakfast",       category="feeding",     duration_minutes=10, priority="high",   time_of_day_preference="morning"))
mochi.add_task(Task(title="Joint Supplement",category="medication",  duration_minutes=5,  priority="high",   time_of_day_preference="morning"))
mochi.add_task(Task(title="Afternoon Play",  category="enrichment",  duration_minutes=20, priority="medium", time_of_day_preference="afternoon"))
mochi.add_task(Task(title="Evening Walk",    category="walk",        duration_minutes=25, priority="medium", time_of_day_preference="evening"))

# --- Tasks for Luna ---
luna.add_task(Task(title="Breakfast",        category="feeding",     duration_minutes=5,  priority="high",   time_of_day_preference="morning"))
luna.add_task(Task(title="Litter Box Clean", category="grooming",    duration_minutes=10, priority="medium", time_of_day_preference="morning"))
luna.add_task(Task(title="Wand Toy Play",    category="enrichment",  duration_minutes=15, priority="low",    time_of_day_preference="afternoon"))

# --- Owner ---
jordan = Owner(
    name="Jordan",
    available_minutes_per_day=90,
    preferred_start_time=time(7, 0),
    preferred_end_time=time(21, 0),
    pets=[mochi, luna],
)

# --- Schedule ---
scheduler = Scheduler(owner=jordan)
schedule = scheduler.generate_schedule()

print("=" * 50)
print("       TODAY'S SCHEDULE — PawPal+")
print("=" * 50)

for entry in schedule:
    print(f"  {entry['start_time']} – {entry['end_time']}  "
          f"[{entry['priority'].upper():6}]  "
          f"{entry['task']} ({entry['pet']}, {entry['duration_minutes']} min)")

print("=" * 50)
print()
print(scheduler.explain_choices())
