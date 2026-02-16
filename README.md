# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

PawPal+ includes several algorithmic improvements to help pet owners manage their day more efficiently:

### Lambda-Based Sorting & Filtering
- **Smart time sorting**: Tasks are sorted using lambda functions that handle HH:MM time strings, automatically placing flexible tasks at the end
- **Priority-first scheduling**: High-priority health tasks (medication, feeding) are guaranteed to be scheduled before lower-priority activities
- **Flexible filtering**: Filter tasks by pet name and completion status using efficient lambda-based filters

### Recurring Task Management
- **Auto-creation**: When you complete a daily or weekly task, the system automatically creates the next occurrence
- **No manual re-entry**: Never forget to add tomorrow's feeding or medication tasks again

### Enhanced Conflict Detection
- **Exact time conflicts**: Detects when two tasks start at the same time (e.g., both pets need feeding at 7:30 AM)
- **Overlapping time ranges**: Considers task duration to catch overlaps (e.g., Luna's playtime 7:50-8:15 overlaps with Mochi's walk 8:00-8:30)
- **Pet context**: Distinguishes between same-pet conflicts and owner conflicts (can't be in two places at once)
- **Detailed messages**: Shows which pets are affected and the exact time ranges involved

These features help busy pet owners avoid scheduling impossible tasks and ensure critical care activities are never missed.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
