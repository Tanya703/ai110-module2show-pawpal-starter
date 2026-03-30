import unittest
from pawpal_system import Task, Pet


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


if __name__ == "__main__":
    unittest.main()
