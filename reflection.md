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

The scheduler considers three constraints:

1. **Time budget** — the owner's `available_minutes_per_day` is a hard cap and no tasks can be scheduled once it is reached

2. **Task priority** — each task is rated high, medium, or low. Before the budget filter runs, tasks are sorted high → medium → low, so the most important care activities are always considered first and are the last to be dropped.

3. **Time-of-day preference** — tasks declare a preferred slot (morning, afternoon, evening) and an optional `fixed_start_time`. These are soft preferences: `sort_tasks(by="time")` groups tasks into the right part of the day, and `fixed_start_time` pins a task to an exact hour when the owner has an external commitment like a vet appointment.

The time budget is the only true hard constraint — a task that does not fit simply cannot run. Priority was ranked second because it directly encodes the owner's judgment about the pet's health  Time-of-day preference was treated as softest because most pet care tasks have flexibility within a day; the scheduler surfaces conflicts when they arise 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler sorts all tasks by priority (high → medium → low) and then fills the day in that order, stopping when the time budget runs out. This means a high-priority 30-minute task will always be included ahead of three low-priority 5-minute tasks — even if the three short tasks would collectively serve the pet better and still fit within the budget.

In the case with pet scheduling app, the chances of having a lot of high priority tasks is low and also the schedule directly reflects owner preferences. This way the scheduler avoids unnesessary complexity

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude for deisgn brainstorming and design implementation.I also use Claude for debugging, writting code and tests. I noticed that asking specific question, adding constraits and requirements was helful for higher quality output. I also found that highlighting specific line or adding the specific file for the prompt was usefule to add context and improve output

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

In the design process I chose not to accept Claude suggestions. The suggestions were relevant however were out of the scope for this project and overcomplecated the design. It suggested additional methods that sounded like a greate add-on but made the implemetion complex. I verified the Ai suggestions by reviewing the code, refering back to project requirements and asking follow-up questions to understand the code before accepting it

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The test suite has 25 tests that check the three main features added in this module:

- **Sorting** — tasks come back in the right order (high priority first, or morning before afternoon before evening)
- **Recurring tasks** — marking a daily task complete creates a new one for tomorrow; weekly tasks push out 7 days; one-time tasks don't create anything new
- **Conflict detection** — two tasks at the same time trigger a warning; tasks that don't overlap don't

It also covers a few edge cases that are easy to miss: a pet with no tasks, a task that exactly fills the time budget, and what happens when every task is already completed

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

★★★ 3/5 — All 25 tests pass and the core logic feels solid. Additional teting is needed through UI and edge cases with users. After i tested through UI i found mulltiple cases of things not working properly or not being desplayed in UI. Nex Time I would test the complete/incomplete task attribute, reoccuring tasks as well as test how various types of inputs are being processed.


---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The implementation od core functions went well as well as following through through the start-to-finish process of creating an app

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would tweak the functions that not fully working such as reoccuring tasks and complete/not complete attributes

I would also be more intetional with designing a scheduling algorithm - think through the edge cases and user needs

I would also working on memory, adding multiple pets and planning for multiple days.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

My key take away is that Claude can be used on every stage of creating the project, from design to implementation to testing. I also learnt taht rushes through accepting Claude suggestions with understanding and thoroghly revewing them can result in inconcetencies and a lot of time requered to go back and fix review, fix can increase the complexity of the code