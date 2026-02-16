# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

1. Add and manage pets — The user can enter basic information about their pet (name, species, age) so tasks can be organized by each pet’s needs.
2. Create and update care tasks — The user can add tasks like feeding, walks, medications, or grooming, including duration, priority, and timing so the system understands what needs to be done.
3. Generate and review a daily care plan — The user can view a prioritized schedule for the day that fits their available time, along with explanations or warnings (like conflicts or tasks that couldn’t fit).

Owner, Pet, Task, Scheduler

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes I made a change clarifying the relationship between pets and the tasks. Tasks do not store a reference to their pet to avoid unnecessary coupling and circular dependencies. Instead, pets own their tasks, and the scheduler accesses tasks through pets. This keeps the system simple and easier to maintain.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- The scheduler considers: (1) time budget (owner's available minutes), (2) task priority (1-5 scale), and (3) task timing (due_time vs flexible). Priority was chosen as the most important because health/safety tasks (medication, feeding) must take precedence over optional activities.
- I prioritized simplicity and safety: the scheduler uses a greedy approach that guarantees high-priority tasks are scheduled first, even if this doesn't always maximize the total number of tasks completed.

**b. Tradeoffs**

- **Tradeoff**: The scheduler uses a greedy algorithm (sorts by priority, adds tasks until time runs out) rather than optimal bin-packing. This can waste time - for example, with 60 min available and tasks of 50 min (priority 5), 30 min (priority 4), and 25 min (priority 3), it only schedules the 50-min task instead of the optimal 30+25 min combination.
- **Why reasonable**: For pet care, missing a high-priority medication is worse than missing lower-priority playtime. The greedy approach is simple, predictable, and prioritizes safety over efficiency - which is the right choice for caring for pets.

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
