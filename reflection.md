# PawPal+ Project Reflection

## 1. System Design

**a. Core user actions**

The system is designed around three primary actions that a user should be able to perform:

1. **Add and manage pet information** - A user can enter and update basic information about their pet (name, type, age, special needs) and their own availability/constraints. This establishes the context for all scheduling decisions.

2. **Add and edit pet care tasks** - A user can define specific pet care tasks (walks, feeding, medication, grooming, enrichment activities) with essential details like duration in minutes and priority level. This builds the list of activities that need to be scheduled.

3. **Generate and view the daily schedule** - A user can request a daily plan that intelligently schedules all their pet care tasks based on the constraints (owner availability, task timing), priorities, and preferences. The system displays the resulting schedule and explains the reasoning behind the scheduling decisions.

**b. Initial design**

The system uses four classes: `Pet`, `Task`, `Owner`, and `Scheduler`.

- **`Pet`** is a dataclass that holds descriptive information about the animal (name, species, age, special needs). Its only responsibility is to represent the pet's profile so the scheduler has context.

- **`Task`** is a dataclass representing a single care activity. It stores what needs to happen (title, category), how long it takes (duration_minutes), how important it is (priority), and an optional preferred time of day. It knows whether it is high priority but does not decide when it runs.

- **`Owner`** is a dataclass that holds the owner's name, their available time budget for the day, and their preferred start and end times. It owns a reference to their `Pet`. Its responsibility is to provide the time constraints that the scheduler must respect.

- **`Scheduler`** is a regular class (not a dataclass) because it contains behavior, not just data. It takes an `Owner`, a `Pet`, and a list of `Task` objects and is responsible for producing a daily plan. It filters tasks that won't fit in the available time, sorts by priority, and generates an explanation of the choices made.

**c. Design changes**

After reviewing the initial skeleton, four changes were made before any logic was implemented:

1. **Removed `pet` as a parameter from `Scheduler`** — The original design passed `owner` and `pet` separately to `Scheduler`, but `Owner` already holds a reference to `Pet`. Having both created two sources of truth that could fall out of sync. The fix was to remove the `pet` parameter and have `Scheduler` read `owner.pet` directly.

2. **Made `Owner.pet` a required field** — It was originally optional (`pet: Pet = None`), which would allow an `Owner` to exist without a pet. Since the entire app is built around caring for a pet, a petless owner makes no sense. Removing the default forces callers to always provide one.

3. **Removed `Owner.has_enough_time()`** — This method overlapped with `Scheduler.filter_tasks_by_time()`. Both were checking whether tasks fit within available time. Keeping both would split constraint logic across two classes. All scheduling decisions now belong to `Scheduler`.

4. **Changed time fields from `str` to `datetime.time`** — `preferred_start_time` and `preferred_end_time` were plain strings (e.g. `"07:00"`). String comparison is unreliable for scheduling math. Switching to `datetime.time` makes it straightforward to calculate whether a task fits within the owner's available window.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
