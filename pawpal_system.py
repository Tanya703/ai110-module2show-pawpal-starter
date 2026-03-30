from dataclasses import dataclass
from typing import Optional


@dataclass
class Pet:
    name: str
    species: str               # "dog", "cat", "other"
    age: int
    special_needs: Optional[str] = None

    def get_summary(self) -> str:
        pass


@dataclass
class Task:
    title: str
    category: str              # "walk", "feeding", "medication", "grooming", "enrichment"
    duration_minutes: int
    priority: str              # "low", "medium", "high"
    time_of_day_preference: Optional[str] = None  # "morning", "afternoon", "evening"

    def is_high_priority(self) -> bool:
        pass

    def to_dict(self) -> dict:
        pass


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int
    preferred_start_time: str  # e.g. "07:00"
    preferred_end_time: str    # e.g. "21:00"
    pet: Pet = None

    def get_time_window(self) -> tuple:
        pass

    def has_enough_time(self, tasks: list[Task]) -> bool:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def generate_schedule(self) -> list:
        pass

    def filter_tasks_by_time(self) -> list[Task]:
        pass

    def sort_by_priority(self) -> list[Task]:
        pass

    def explain_choices(self) -> str:
        pass
