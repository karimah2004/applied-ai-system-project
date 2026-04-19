"""
AI Advisor for PawPal+: connects RAG outputs to the Scheduler.
Generates breed-appropriate task suggestions and answers free-form questions.
"""

import json
from rag_engine import retrieve_chunks, answer_breed_question, MEDICAL_DISCLAIMER, _model
from pawpal_system import Task, Pet


BREED_TASK_TEMPLATES: dict[str, list[dict]] = {
    "golden_retriever.md": [
        {"title": "Morning walk", "category": "exercise", "duration_minutes": 45, "priority": 5, "due_time": "08:00", "frequency": "daily"},
        {"title": "Evening walk", "category": "exercise", "duration_minutes": 30, "priority": 4, "due_time": "18:00", "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 15, "priority": 3, "due_time": None, "frequency": "weekly"},
        {"title": "Ear check", "category": "health", "duration_minutes": 5, "priority": 4, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "17:30", "frequency": "daily"},
    ],
    "labrador_retriever.md": [
        {"title": "Morning walk/run", "category": "exercise", "duration_minutes": 45, "priority": 5, "due_time": "08:00", "frequency": "daily"},
        {"title": "Evening walk", "category": "exercise", "duration_minutes": 30, "priority": 4, "due_time": "18:00", "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 10, "priority": 2, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "17:30", "frequency": "daily"},
        {"title": "Ear check", "category": "health", "duration_minutes": 5, "priority": 4, "due_time": None, "frequency": "weekly"},
    ],
    "french_bulldog.md": [
        {"title": "Short morning walk", "category": "exercise", "duration_minutes": 15, "priority": 4, "due_time": "07:30", "frequency": "daily"},
        {"title": "Short evening walk", "category": "exercise", "duration_minutes": 15, "priority": 3, "due_time": "19:00", "frequency": "daily"},
        {"title": "Facial fold cleaning", "category": "hygiene", "duration_minutes": 5, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 10, "priority": 2, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "07:00", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "18:00", "frequency": "daily"},
    ],
    "bulldog.md": [
        {"title": "Gentle morning walk", "category": "exercise", "duration_minutes": 15, "priority": 4, "due_time": "07:30", "frequency": "daily"},
        {"title": "Wrinkle cleaning", "category": "hygiene", "duration_minutes": 10, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 10, "priority": 2, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "07:00", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "18:00", "frequency": "daily"},
    ],
    "corgi.md": [
        {"title": "Morning walk", "category": "exercise", "duration_minutes": 30, "priority": 5, "due_time": "08:00", "frequency": "daily"},
        {"title": "Evening play session", "category": "exercise", "duration_minutes": 20, "priority": 4, "due_time": "18:00", "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 15, "priority": 3, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "17:30", "frequency": "daily"},
    ],
    "poodle.md": [
        {"title": "Morning walk", "category": "exercise", "duration_minutes": 30, "priority": 5, "due_time": "08:00", "frequency": "daily"},
        {"title": "Mental enrichment / training", "category": "enrichment", "duration_minutes": 15, "priority": 4, "due_time": None, "frequency": "daily"},
        {"title": "Daily brushing", "category": "grooming", "duration_minutes": 15, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Ear check", "category": "health", "duration_minutes": 5, "priority": 4, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "17:30", "frequency": "daily"},
    ],
    "german_shepherd.md": [
        {"title": "Morning run/walk", "category": "exercise", "duration_minutes": 60, "priority": 5, "due_time": "07:00", "frequency": "daily"},
        {"title": "Evening walk", "category": "exercise", "duration_minutes": 45, "priority": 4, "due_time": "18:00", "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 15, "priority": 3, "due_time": None, "frequency": "weekly"},
        {"title": "Training session", "category": "enrichment", "duration_minutes": 20, "priority": 4, "due_time": None, "frequency": "daily"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "06:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "17:00", "frequency": "daily"},
    ],
    "beagle.md": [
        {"title": "Leashed scent walk", "category": "exercise", "duration_minutes": 30, "priority": 5, "due_time": "08:00", "frequency": "daily"},
        {"title": "Evening walk", "category": "exercise", "duration_minutes": 20, "priority": 4, "due_time": "18:00", "frequency": "daily"},
        {"title": "Ear check", "category": "health", "duration_minutes": 5, "priority": 5, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 10, "priority": 5, "due_time": "17:30", "frequency": "daily"},
    ],
    "maine_coon.md": [
        {"title": "Interactive play session", "category": "exercise", "duration_minutes": 20, "priority": 4, "due_time": None, "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 10, "priority": 4, "due_time": None, "frequency": "weekly"},
        {"title": "Ear check", "category": "health", "duration_minutes": 5, "priority": 3, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "17:30", "frequency": "daily"},
        {"title": "Water fountain refill", "category": "hygiene", "duration_minutes": 5, "priority": 3, "due_time": None, "frequency": "daily"},
    ],
    "siamese.md": [
        {"title": "Interactive play session", "category": "exercise", "duration_minutes": 15, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 5, "priority": 2, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "17:30", "frequency": "daily"},
        {"title": "Dental brushing", "category": "hygiene", "duration_minutes": 5, "priority": 4, "due_time": None, "frequency": "weekly"},
    ],
    "persian.md": [
        {"title": "Daily brushing", "category": "grooming", "duration_minutes": 15, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Face/eye cleaning", "category": "hygiene", "duration_minutes": 5, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Gentle play session", "category": "exercise", "duration_minutes": 15, "priority": 3, "due_time": None, "frequency": "daily"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "17:30", "frequency": "daily"},
        {"title": "Dental brushing", "category": "hygiene", "duration_minutes": 5, "priority": 5, "due_time": None, "frequency": "weekly"},
    ],
    "yorkshire_terrier.md": [
        {"title": "Short walk", "category": "exercise", "duration_minutes": 15, "priority": 4, "due_time": "08:00", "frequency": "daily"},
        {"title": "Daily brushing", "category": "grooming", "duration_minutes": 10, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Dental brushing", "category": "hygiene", "duration_minutes": 5, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Feeding (x3 small meals)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "08:00", "frequency": "daily"},
    ],
    "shih_tzu.md": [
        {"title": "Leisurely walk", "category": "exercise", "duration_minutes": 20, "priority": 4, "due_time": "08:00", "frequency": "daily"},
        {"title": "Daily brushing", "category": "grooming", "duration_minutes": 15, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Face cleaning", "category": "hygiene", "duration_minutes": 5, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Dental brushing", "category": "hygiene", "duration_minutes": 5, "priority": 5, "due_time": None, "frequency": "daily"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "17:30", "frequency": "daily"},
    ],
    "bengal.md": [
        {"title": "Interactive play session (morning)", "category": "exercise", "duration_minutes": 20, "priority": 5, "due_time": "08:00", "frequency": "daily"},
        {"title": "Interactive play session (evening)", "category": "exercise", "duration_minutes": 20, "priority": 5, "due_time": "19:00", "frequency": "daily"},
        {"title": "Puzzle feeder", "category": "enrichment", "duration_minutes": 10, "priority": 4, "due_time": None, "frequency": "daily"},
        {"title": "Brushing", "category": "grooming", "duration_minutes": 5, "priority": 2, "due_time": None, "frequency": "weekly"},
        {"title": "Feeding (morning)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "07:30", "frequency": "daily"},
        {"title": "Feeding (evening)", "category": "feeding", "duration_minutes": 5, "priority": 5, "due_time": "17:30", "frequency": "daily"},
    ],
}

from rag_engine import BREED_FILE_MAP


def suggest_tasks_for_breed(breed_name: str, pet_age_years: float) -> list[dict]:
    """
    Return a list of suggested task dicts for a given breed and pet age.
    Each dict has the same fields as Task constructor kwargs.
    Falls back to AI-generated suggestions if breed has no template.
    """
    key = breed_name.strip().lower()
    filename = BREED_FILE_MAP.get(key)
    if not filename:
        for alias, fname in BREED_FILE_MAP.items():
            if key in alias or alias in key:
                filename = fname
                break

    if filename and filename in BREED_TASK_TEMPLATES:
        tasks = list(BREED_TASK_TEMPLATES[filename])
        tasks = _adjust_for_age(tasks, pet_age_years, filename)
        return tasks

    return _ai_generated_tasks(breed_name, pet_age_years)


def _adjust_for_age(tasks: list[dict], age_years: float, filename: str) -> list[dict]:
    """Adjust exercise intensity/duration based on pet age."""
    adjusted = []
    for t in tasks:
        task = dict(t)
        is_puppy = age_years < 1
        is_senior = _is_senior(age_years, filename)

        if task["category"] == "exercise":
            if is_puppy:
                task["duration_minutes"] = max(10, task["duration_minutes"] // 2)
                task["title"] = "Puppy: " + task["title"]
            elif is_senior:
                task["duration_minutes"] = max(10, int(task["duration_minutes"] * 0.7))
                task["title"] = "Gentle: " + task["title"]

        adjusted.append(task)
    return adjusted


def _is_senior(age_years: float, filename: str) -> bool:
    cat_breeds = {"maine_coon.md", "siamese.md", "persian.md", "bengal.md"}
    threshold = 10 if filename in cat_breeds else 7
    return age_years >= threshold


def _ai_generated_tasks(breed_name: str, age_years: float) -> list[dict]:
    """Use Claude to suggest tasks for breeds not in the knowledge base."""
    chunks, canonical = retrieve_chunks(breed_name, "exercise grooming feeding health care")
    context = "\n\n".join(chunks) if chunks else "No breed-specific data available."

    system_prompt = (
        "You are a pet care expert. Generate a JSON array of 4–6 daily/weekly care tasks for the given breed. "
        "Each task must be a JSON object with these exact keys: "
        "title (string), category (one of: exercise/feeding/health/grooming/enrichment/hygiene), "
        "duration_minutes (integer), priority (1–5 integer), "
        "due_time (string HH:MM or null), frequency (daily or weekly). "
        "Return ONLY valid JSON array, no explanation."
    )

    response = _model.generate_content(
        f"{system_prompt}\n\nBreed: {breed_name}\nAge: {age_years} years\n\n"
        f"Breed context (if available):\n{context}"
    )

    try:
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        tasks = json.loads(text)
        return tasks if isinstance(tasks, list) else []
    except (json.JSONDecodeError, KeyError):
        return []


def answer_question(breed_name: str, question: str) -> str:
    """
    Answer a free-form question about a breed using RAG.
    Delegates to rag_engine.answer_breed_question.
    """
    return answer_breed_question(breed_name, question)


def tasks_to_Task_objects(suggestions: list[dict]) -> list[Task]:
    """Convert suggestion dicts to Task objects."""
    tasks = []
    for s in suggestions:
        try:
            tasks.append(Task(
                title=s["title"],
                category=s.get("category", "enrichment"),
                duration_minutes=int(s.get("duration_minutes", 15)),
                priority=int(s.get("priority", 3)),
                due_time=s.get("due_time"),
                frequency=s.get("frequency", "daily"),
            ))
        except (KeyError, TypeError, ValueError):
            continue
    return tasks
