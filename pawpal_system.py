from dataclasses import dataclass, field
from datetime import time
from typing import Optional


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    title: str
    category: str              # "walk", "feeding", "medication", "grooming", "enrichment"
    duration_minutes: int
    priority: str              # "low", "medium", "high"
    time_of_day_preference: Optional[str] = None  # "morning", "afternoon", "evening"
    completed: bool = False

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        return self.priority == "high"

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "category": self.category,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "time_of_day_preference": self.time_of_day_preference,
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

    def sort_by_priority(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Return tasks sorted from highest to lowest priority."""
        return sorted(tasks, key=lambda pt: PRIORITY_ORDER.get(pt[1].priority, 99))

    def filter_tasks_by_time(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Keep tasks that fit within the owner's available minutes budget."""
        budget = self.owner.available_minutes_per_day
        selected = []
        used = 0
        for pet, task in tasks:
            if used + task.duration_minutes <= budget:
                selected.append((pet, task))
                used += task.duration_minutes
        return selected

    def generate_schedule(self) -> list[dict]:
        """
        Builds a daily schedule across all pets.
        Steps: collect → sort by priority → filter to fit time budget → assign start times.
        """
        all_tasks = self.owner.get_all_tasks()
        pending = [(pet, task) for pet, task in all_tasks if not task.completed]
        sorted_tasks = self.sort_by_priority(pending)
        scheduled_tasks = self.filter_tasks_by_time(sorted_tasks)

        schedule = []
        start_h = self.owner.preferred_start_time.hour
        start_m = self.owner.preferred_start_time.minute
        current_minutes = start_h * 60 + start_m

        for pet, task in scheduled_tasks:
            slot_h, slot_m = divmod(current_minutes, 60)
            end_minutes = current_minutes + task.duration_minutes
            end_h, end_m = divmod(end_minutes, 60)
            schedule.append({
                "pet": pet.name,
                "task": task.title,
                "category": task.category,
                "priority": task.priority,
                "start_time": f"{slot_h:02d}:{slot_m:02d}",
                "end_time": f"{end_h:02d}:{end_m:02d}",
                "duration_minutes": task.duration_minutes,
            })
            current_minutes = end_minutes

        return schedule

    def explain_choices(self) -> str:
        """Returns a plain-English explanation of the scheduling decisions."""
        all_tasks = self.owner.get_all_tasks()
        pending = [(pet, task) for pet, task in all_tasks if not task.completed]
        sorted_tasks = self.sort_by_priority(pending)
        scheduled = self.filter_tasks_by_time(sorted_tasks)
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
