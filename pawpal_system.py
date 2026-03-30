from dataclasses import dataclass, field
from datetime import date, time, timedelta
from itertools import combinations
from typing import Optional


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}
FREQUENCY_DELTA = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


@dataclass
class Task:
    title: str
    category: str              # "walk", "feeding", "medication", "grooming", "enrichment"
    duration_minutes: int
    priority: str              # "low", "medium", "high"
    time_of_day_preference: Optional[str] = None  # "morning", "afternoon", "evening"
    frequency: Optional[str] = None               # "daily", "weekly", or None (one-time)
    due_date: Optional[date] = None               # date this task is due
    fixed_start_time: Optional[time] = None       # pin to a specific clock time, e.g. time(8, 0)
    completed: bool = False

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        return self.priority == "high"

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> Optional["Task"]:
        """Return a new pending Task for the next occurrence, or None if one-time.

        Uses FREQUENCY_DELTA to calculate the next due date:
          - "daily"  → due_date + timedelta(days=1)
          - "weekly" → due_date + timedelta(weeks=1)
        If due_date is not set, today is used as the base.
        """
        delta = FREQUENCY_DELTA.get(self.frequency)
        if delta is None:
            return None
        base = self.due_date if self.due_date is not None else date.today()
        return Task(
            title=self.title,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            time_of_day_preference=self.time_of_day_preference,
            frequency=self.frequency,
            due_date=base + delta,
            completed=False,
        )

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "category": self.category,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "time_of_day_preference": self.time_of_day_preference,
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "fixed_start_time": self.fixed_start_time.strftime("%H:%M") if self.fixed_start_time else None,
            "completed": self.completed,
        }


@dataclass
class Pet:
    name: str
    species: str               # "dog", "cat", "other"
    age: int
    special_needs: Optional[str] = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str):
        """Remove all tasks matching the given title from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def get_summary(self) -> str:
        """Return a human-readable one-line summary of this pet."""
        needs = f", special needs: {self.special_needs}" if self.special_needs else ""
        return f"{self.name} ({self.species}, age {self.age}{needs})"


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int
    preferred_start_time: time        # e.g. time(7, 0)
    preferred_end_time: time          # e.g. time(21, 0)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Append a pet to this owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, name: str):
        """Remove all pets matching the given name from this owner's pet list."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Returns all tasks across all pets as (pet, task) pairs."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_time_window(self) -> tuple[time, time]:
        """Return the owner's preferred start and end times as a tuple."""
        return (self.preferred_start_time, self.preferred_end_time)


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    @staticmethod
    def _to_min(t: time) -> int:
        """Convert a time object to total minutes since midnight."""
        return t.hour * 60 + t.minute

    def mark_task_complete(self, pet: Pet, task: Task) -> Optional[Task]:
        """Mark a task complete and, if it recurs, add the next occurrence to the pet.

        Calls task.mark_complete() then task.next_occurrence(). If a next
        occurrence exists it is appended to pet.tasks so it appears in future
        schedule runs.

        Args:
            pet:  The Pet that owns the task (receives the new occurrence).
            task: The Task to mark as completed.

        Returns:
            The newly created Task for the next occurrence, or None if the
            task has no frequency (i.e. it is a one-time task).
        """
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def sort_tasks(
        self,
        tasks: list[tuple[Pet, Task]],
        *,
        by: str = "priority",
    ) -> list[tuple[Pet, Task]]:
        """Return a new sorted list of (Pet, Task) pairs without modifying the original.

        Sorting is driven by module-level lookup dicts (PRIORITY_ORDER, TIME_ORDER)
        so unknown values fall to the end (sentinel 99) rather than raising an error.

        Args:
            tasks: List of (Pet, Task) pairs to sort.
            by:    Sort strategy — one of:
                     "priority"  high → medium → low (default)
                     "time"      morning → afternoon → evening, with priority
                                 as a tiebreaker within each time slot.

        Returns:
            A new list of (Pet, Task) pairs in the requested order.
        """
        keys = {
            "priority": lambda pt: PRIORITY_ORDER.get(pt[1].priority, 99),
            "time": lambda pt: (
                TIME_ORDER.get(pt[1].time_of_day_preference, 99),
                PRIORITY_ORDER.get(pt[1].priority, 99),
            ),
        }
        return sorted(tasks, key=keys[by])

    def filter_tasks(
        self,
        tasks: list[tuple[Pet, Task]],
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter (Pet, Task) pairs by pet name and/or completion status in one pass.

        Both conditions are evaluated together in a single list comprehension so
        the input list is iterated only once regardless of how many filters are active.
        Omitting a parameter leaves that dimension unfiltered.

        Args:
            tasks:     List of (Pet, Task) pairs to filter.
            pet_name:  If given, keep only pairs where pet.name == pet_name.
            completed: If True, keep only completed tasks.
                       If False, keep only pending (not yet completed) tasks.
                       If None (default), keep tasks regardless of status.

        Returns:
            A new list containing only the (Pet, Task) pairs that satisfy
            all supplied conditions. Original list is not modified.
        """
        return [
            (pet, task) for pet, task in tasks
            if (pet_name is None or pet.name == pet_name)
            and (completed is None or task.completed == completed)
        ]

    def filter_tasks_by_time(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Select tasks greedily until the owner's daily time budget is exhausted.

        Iterates tasks in the order given (caller is responsible for pre-sorting
        by priority) and accumulates each task whose duration fits within the
        remaining budget. Tasks that would overflow the budget are skipped —
        no backtracking or rearranging is attempted.

        Args:
            tasks: (Pet, Task) pairs in priority order to consider for scheduling.

        Returns:
            A subset of tasks whose total duration_minutes does not exceed
            owner.available_minutes_per_day. Order is preserved from the input.
        """
        budget = self.owner.available_minutes_per_day
        selected = []
        used = 0
        for pet, task in tasks:
            if used + task.duration_minutes <= budget:
                selected.append((pet, task))
                used += task.duration_minutes
        return selected

    def generate_schedule(self) -> list[dict]:
        """Build and return a daily schedule across all of the owner's pets.

        Pipeline:
            1. Collect all (Pet, Task) pairs from every pet.
            2. Filter to pending tasks only (completed=False).
            3. Sort by priority (high → medium → low).
            4. Greedily select tasks that fit within the time budget.
            5. Assign wall-clock start/end times sequentially from
               owner.preferred_start_time. Tasks with a fixed_start_time
               are pinned to that time instead of the running clock.

        Returns:
            A list of schedule-entry dicts, one per scheduled task, each with:
                pet             (str)  Pet's name.
                task            (str)  Task title.
                category        (str)  Task category (e.g. "walk", "feeding").
                priority        (str)  "high", "medium", or "low".
                start_time      (str)  Wall-clock start in "HH:MM" format.
                end_time        (str)  Wall-clock end in "HH:MM" format.
                start_min       (int)  Start as total minutes since midnight.
                end_min         (int)  End as total minutes since midnight.
                duration_minutes(int)  Task duration in minutes.
        """
        all_tasks = self.owner.get_all_tasks()
        pending = self.filter_tasks(all_tasks, completed=False)
        sorted_tasks = self.sort_tasks(pending, by="priority")
        scheduled_tasks = self.filter_tasks_by_time(sorted_tasks)

        schedule = []
        current_minutes = self._to_min(self.owner.preferred_start_time)

        for pet, task in scheduled_tasks:
            task_start = self._to_min(task.fixed_start_time) if task.fixed_start_time else current_minutes
            task_end = task_start + task.duration_minutes
            slot_h, slot_m = divmod(task_start, 60)
            end_h, end_m = divmod(task_end, 60)
            schedule.append({
                "pet": pet.name,
                "task": task.title,
                "category": task.category,
                "priority": task.priority,
                "start_time": f"{slot_h:02d}:{slot_m:02d}",
                "end_time": f"{end_h:02d}:{end_m:02d}",
                "start_min": task_start,
                "end_min": task_end,
                "duration_minutes": task.duration_minutes,
            })
            if task.fixed_start_time is None:
                current_minutes = task_end

        return schedule

    def detect_conflicts(self, schedule: list[dict]) -> list[str]:
        """Detect overlapping time windows in a generated schedule.

        Uses itertools.combinations to iterate every unique pair of entries
        (O(n²)) and applies the standard interval-overlap condition:
            overlap exists when  start_A < end_B  AND  start_B < end_A
        Integer start_min/end_min fields from generate_schedule() are used
        directly — no string parsing is required.

        This method never raises; it always returns a list (possibly empty).
        It is intended as a warning layer, not a hard constraint enforcer.

        Args:
            schedule: The list of schedule-entry dicts returned by
                      generate_schedule(). Each entry must contain
                      start_min, end_min, task, and pet keys.

        Returns:
            A list of human-readable warning strings, one per conflicting pair.
            Returns an empty list if no conflicts are found.
        """
        warnings = []
        for a, b in combinations(schedule, 2):
            if a["start_min"] < b["end_min"] and b["start_min"] < a["end_min"]:
                warnings.append(
                    f"  WARNING: '{a['task']}' ({a['pet']}, {a['start_time']}-{a['end_time']}) "
                    f"overlaps with '{b['task']}' ({b['pet']}, {b['start_time']}-{b['end_time']})"
                )
        return warnings

    def explain_choices(self) -> str:
        """Returns a plain-English explanation of the scheduling decisions."""
        all_tasks = self.owner.get_all_tasks()
        pending = self.filter_tasks(all_tasks, completed=False)
        scheduled = self.filter_tasks_by_time(self.sort_tasks(pending, by="priority"))
        scheduled_titles = {task.title for _, task in scheduled}
        dropped = [task for _, task in pending if task.title not in scheduled_titles]

        lines = [f"Schedule for {self.owner.name} | budget: {self.owner.available_minutes_per_day} min\n"]
        lines.append("Included tasks (sorted by priority):")
        for pet, task in scheduled:
            lines.append(f"  - [{task.priority.upper()}] {task.title} for {pet.name} ({task.duration_minutes} min)")

        if dropped:
            lines.append("\nDropped due to time constraints:")
            for task in dropped:
                lines.append(f"  - {task.title} ({task.duration_minutes} min, {task.priority} priority)")

        return "\n".join(lines)
