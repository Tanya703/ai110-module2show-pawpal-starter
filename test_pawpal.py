import unittest
from datetime import date, time, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(pets, budget=120):
    return Owner(
        name="Jordan",
        available_minutes_per_day=budget,
        preferred_start_time=time(7, 0),
        preferred_end_time=time(21, 0),
        pets=pets,
    )


def make_pet(tasks=None):
    pet = Pet(name="Mochi", species="dog", age=3)
    for t in (tasks or []):
        pet.add_task(t)
    return pet


# ---------------------------------------------------------------------------
# Existing tests (preserved)
# ---------------------------------------------------------------------------

class TestTaskCompletion(unittest.TestCase):
    def test_mark_complete_changes_status(self):
        task = Task(title="Morning walk", category="walk", duration_minutes=30, priority="high")
        self.assertFalse(task.completed)
        task.mark_complete()
        self.assertTrue(task.completed)


class TestPetTaskAddition(unittest.TestCase):
    def test_add_task_increases_task_count(self):
        pet = Pet(name="Buddy", species="dog", age=3)
        self.assertEqual(len(pet.tasks), 0)
        task = Task(title="Feeding", category="feeding", duration_minutes=10, priority="medium")
        pet.add_task(task)
        self.assertEqual(len(pet.tasks), 1)


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

class TestSortByPriority(unittest.TestCase):
    def setUp(self):
        pet = make_pet()
        self.scheduler = Scheduler(make_owner([pet]))
        self.low  = (pet, Task(title="Play",    category="enrichment", duration_minutes=15, priority="low"))
        self.med  = (pet, Task(title="Groom",   category="grooming",   duration_minutes=10, priority="medium"))
        self.high = (pet, Task(title="Meds",    category="medication", duration_minutes=5,  priority="high"))

    def test_priority_order_high_first(self):
        result = self.scheduler.sort_tasks([self.low, self.med, self.high], by="priority")
        priorities = [t.priority for _, t in result]
        self.assertEqual(priorities, ["high", "medium", "low"])

    def test_already_sorted_unchanged(self):
        ordered = [self.high, self.med, self.low]
        result = self.scheduler.sort_tasks(ordered, by="priority")
        self.assertEqual([t.priority for _, t in result], ["high", "medium", "low"])

    def test_returns_new_list(self):
        original = [self.low, self.high]
        result = self.scheduler.sort_tasks(original, by="priority")
        self.assertIsNot(result, original)


class TestSortByTime(unittest.TestCase):
    def setUp(self):
        pet = make_pet()
        self.scheduler = Scheduler(make_owner([pet]))
        self.morning   = (pet, Task(title="Breakfast", category="feeding",     duration_minutes=10, priority="high",   time_of_day_preference="morning"))
        self.afternoon = (pet, Task(title="Play",      category="enrichment",  duration_minutes=20, priority="medium", time_of_day_preference="afternoon"))
        self.evening   = (pet, Task(title="Walk",      category="walk",        duration_minutes=25, priority="medium", time_of_day_preference="evening"))
        self.no_pref   = (pet, Task(title="Groom",     category="grooming",    duration_minutes=10, priority="low",    time_of_day_preference=None))

    def test_chronological_order(self):
        shuffled = [self.evening, self.no_pref, self.morning, self.afternoon]
        result = self.scheduler.sort_tasks(shuffled, by="time")
        slots = [t.time_of_day_preference for _, t in result]
        self.assertEqual(slots, ["morning", "afternoon", "evening", None])

    def test_priority_tiebreaker_within_slot(self):
        pet = make_pet()
        high_morning = (pet, Task(title="Meds",      category="medication", duration_minutes=5,  priority="high",   time_of_day_preference="morning"))
        low_morning  = (pet, Task(title="Brush",     category="grooming",   duration_minutes=10, priority="low",    time_of_day_preference="morning"))
        result = self.scheduler.sort_tasks([low_morning, high_morning], by="time")
        self.assertEqual(result[0][1].priority, "high")


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

class TestRecurrence(unittest.TestCase):
    def setUp(self):
        self.today = date.today()

    def test_daily_task_next_due_is_tomorrow(self):
        task = Task(title="Meds", category="medication", duration_minutes=5,
                    priority="high", frequency="daily", due_date=self.today)
        next_task = task.next_occurrence()
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task.due_date, self.today + timedelta(days=1))

    def test_weekly_task_next_due_is_seven_days(self):
        task = Task(title="Bath", category="grooming", duration_minutes=20,
                    priority="medium", frequency="weekly", due_date=self.today)
        next_task = task.next_occurrence()
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task.due_date, self.today + timedelta(weeks=1))

    def test_one_time_task_returns_none(self):
        task = Task(title="Vet", category="grooming", duration_minutes=30,
                    priority="high", frequency=None)
        self.assertIsNone(task.next_occurrence())

    def test_next_occurrence_is_not_completed(self):
        task = Task(title="Meds", category="medication", duration_minutes=5,
                    priority="high", frequency="daily", due_date=self.today)
        next_task = task.next_occurrence()
        self.assertFalse(next_task.completed)

    def test_next_occurrence_copies_all_fields(self):
        task = Task(title="Walk", category="walk", duration_minutes=30, priority="high",
                    time_of_day_preference="morning", frequency="daily", due_date=self.today)
        next_task = task.next_occurrence()
        self.assertEqual(next_task.title,                task.title)
        self.assertEqual(next_task.category,             task.category)
        self.assertEqual(next_task.duration_minutes,     task.duration_minutes)
        self.assertEqual(next_task.time_of_day_preference, task.time_of_day_preference)
        self.assertEqual(next_task.frequency,            task.frequency)

    def test_mark_task_complete_appends_next_occurrence(self):
        task = Task(title="Meds", category="medication", duration_minutes=5,
                    priority="high", frequency="daily", due_date=self.today)
        pet = make_pet([task])
        scheduler = Scheduler(make_owner([pet]))
        scheduler.mark_task_complete(pet, task)
        self.assertEqual(len(pet.tasks), 2)
        self.assertTrue(pet.tasks[0].completed)
        self.assertFalse(pet.tasks[1].completed)
        self.assertEqual(pet.tasks[1].due_date, self.today + timedelta(days=1))

    def test_mark_task_complete_one_time_does_not_append(self):
        task = Task(title="Vet", category="grooming", duration_minutes=30,
                    priority="high", frequency=None)
        pet = make_pet([task])
        scheduler = Scheduler(make_owner([pet]))
        scheduler.mark_task_complete(pet, task)
        self.assertEqual(len(pet.tasks), 1)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

class TestConflictDetection(unittest.TestCase):
    def setUp(self):
        self.pet = make_pet()
        self.scheduler = Scheduler(make_owner([self.pet], budget=200))

    def _entry(self, task_name, pet_name, start_min, duration):
        end_min = start_min + duration
        h, m = divmod(start_min, 60)
        eh, em = divmod(end_min, 60)
        return {
            "task": task_name, "pet": pet_name,
            "start_time": f"{h:02d}:{m:02d}", "end_time": f"{eh:02d}:{em:02d}",
            "start_min": start_min, "end_min": end_min,
        }

    def test_exact_same_start_time_is_conflict(self):
        schedule = [
            self._entry("Vet Check",       "Mochi", 540, 30),  # 09:00–09:30
            self._entry("Grooming Session","Luna",  540, 20),  # 09:00–09:20
        ]
        warnings = self.scheduler.detect_conflicts(schedule)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Vet Check", warnings[0])
        self.assertIn("Grooming Session", warnings[0])

    def test_partial_overlap_is_conflict(self):
        schedule = [
            self._entry("Walk",  "Mochi", 420, 30),  # 07:00–07:30
            self._entry("Meds",  "Luna",  440, 20),  # 07:20–07:40  (overlaps)
        ]
        warnings = self.scheduler.detect_conflicts(schedule)
        self.assertEqual(len(warnings), 1)

    def test_adjacent_tasks_no_conflict(self):
        schedule = [
            self._entry("Breakfast", "Mochi", 420, 10),  # 07:00–07:10
            self._entry("Walk",      "Mochi", 430, 30),  # 07:10–07:40
        ]
        warnings = self.scheduler.detect_conflicts(schedule)
        self.assertEqual(len(warnings), 0)

    def test_no_overlap_no_conflict(self):
        schedule = [
            self._entry("Breakfast", "Mochi", 420, 10),  # 07:00–07:10
            self._entry("Walk",      "Mochi", 480, 30),  # 08:00–08:30
        ]
        warnings = self.scheduler.detect_conflicts(schedule)
        self.assertEqual(len(warnings), 0)

    def test_single_task_no_conflict(self):
        schedule = [self._entry("Meds", "Mochi", 420, 5)]
        warnings = self.scheduler.detect_conflicts(schedule)
        self.assertEqual(len(warnings), 0)

    def test_empty_schedule_no_conflict(self):
        warnings = self.scheduler.detect_conflicts([])
        self.assertEqual(len(warnings), 0)


# ---------------------------------------------------------------------------
# Edge cases — empty pet / budget boundaries
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):
    def test_pet_with_no_tasks_produces_empty_schedule(self):
        pet = make_pet([])
        scheduler = Scheduler(make_owner([pet]))
        self.assertEqual(scheduler.generate_schedule(), [])

    def test_task_exactly_at_budget_is_included(self):
        task = Task(title="Walk", category="walk", duration_minutes=30, priority="high")
        pet = make_pet([task])
        scheduler = Scheduler(make_owner([pet], budget=30))
        schedule = scheduler.generate_schedule()
        self.assertEqual(len(schedule), 1)

    def test_task_one_minute_over_budget_is_excluded(self):
        task = Task(title="Walk", category="walk", duration_minutes=31, priority="high")
        pet = make_pet([task])
        scheduler = Scheduler(make_owner([pet], budget=30))
        schedule = scheduler.generate_schedule()
        self.assertEqual(len(schedule), 0)

    def test_all_completed_tasks_produces_empty_schedule(self):
        task = Task(title="Walk", category="walk", duration_minutes=30, priority="high", completed=True)
        pet = make_pet([task])
        scheduler = Scheduler(make_owner([pet]))
        self.assertEqual(scheduler.generate_schedule(), [])

    def test_filter_tasks_by_pet_name(self):
        mochi = Pet(name="Mochi", species="dog", age=3)
        luna  = Pet(name="Luna",  species="cat", age=5)
        t1 = Task(title="Walk",      category="walk",    duration_minutes=20, priority="high")
        t2 = Task(title="Breakfast", category="feeding", duration_minutes=10, priority="high")
        mochi.add_task(t1)
        luna.add_task(t2)
        scheduler = Scheduler(make_owner([mochi, luna]))
        all_tasks = make_owner([mochi, luna]).get_all_tasks()
        result = scheduler.filter_tasks(all_tasks, pet_name="Mochi")
        self.assertTrue(all(pet.name == "Mochi" for pet, _ in result))
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
