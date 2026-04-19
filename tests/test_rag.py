"""
Reliability tests for PawPal+ RAG system.
Tests: breed-specific grounding, unknown breed fallback, consistency,
task-breed alignment, and vet-referral guardrails.
"""

import pytest
from rag_engine import (
    retrieve_chunks,
    answer_breed_question,
    list_supported_breeds,
    _is_medical_emergency_query,
)
from ai_advisor import suggest_tasks_for_breed, tasks_to_Task_objects


# ---------------------------------------------------------------------------
# 1. Known breeds return breed-specific data, not generic fluff
# ---------------------------------------------------------------------------

class TestBreedSpecificRetrieval:
    def test_golden_retriever_exercise_chunk_contains_breed_data(self):
        chunks, canonical = retrieve_chunks("golden retriever", "how much exercise does this breed need?")
        assert canonical is not None, "Golden Retriever should be found"
        combined = " ".join(chunks).lower()
        assert "60" in combined or "90" in combined, "Should mention specific exercise duration"
        assert "golden" in combined or "retriever" in combined or "exercise" in combined

    def test_bulldog_answer_references_low_intensity(self):
        answer = answer_breed_question("bulldog", "how much exercise does a bulldog need?")
        answer_lower = answer.lower()
        assert "20" in answer_lower or "30" in answer_lower or "gentle" in answer_lower or "low" in answer_lower, \
            "Bulldog answer should reference low exercise requirements"

    def test_german_shepherd_answer_references_high_exercise(self):
        answer = answer_breed_question("german shepherd", "how much exercise does a german shepherd need?")
        answer_lower = answer.lower()
        assert "90" in answer_lower or "120" in answer_lower or "high" in answer_lower or "vigorous" in answer_lower, \
            "German Shepherd answer should reference high exercise requirements"

    def test_poodle_grooming_answer_references_matting(self):
        answer = answer_breed_question("poodle", "how often should I groom my poodle?")
        answer_lower = answer.lower()
        assert "daily" in answer_lower or "mat" in answer_lower or "brush" in answer_lower, \
            "Poodle grooming answer should reference daily brushing / matting"

    def test_corgi_answer_references_spinal_concern(self):
        answer = answer_breed_question("corgi", "what health issues should I watch for?")
        answer_lower = answer.lower()
        assert "disc" in answer_lower or "spine" in answer_lower or "ivdd" in answer_lower or "jump" in answer_lower, \
            "Corgi health answer should reference spinal/disc issues"

    def test_siamese_answer_references_vocalization_or_social(self):
        answer = answer_breed_question("siamese", "what is a siamese cat like?")
        answer_lower = answer.lower()
        assert "vocal" in answer_lower or "social" in answer_lower or "people" in answer_lower, \
            "Siamese temperament answer should reference vocal/social nature"

    def test_answer_cites_source(self):
        answer = answer_breed_question("beagle", "what should I feed my beagle?")
        assert "*Sources:" in answer or "breed profile" in answer.lower(), \
            "Answer should include a source citation"


# ---------------------------------------------------------------------------
# 2. Unknown breeds trigger graceful fallback, no hallucinated breed info
# ---------------------------------------------------------------------------

class TestUnknownBreedFallback:
    def test_unknown_breed_returns_fallback_string(self):
        answer = answer_breed_question("Xoloitzcuintli", "how much exercise does this breed need?")
        assert "not in our breed database" in answer or "not in" in answer.lower() or "don't have" in answer.lower(), \
            "Unknown breed should trigger fallback message"

    def test_unknown_breed_does_not_crash(self):
        try:
            answer = answer_breed_question("Blobfish Terrier", "how do I care for this pet?")
            assert isinstance(answer, str)
            assert len(answer) > 10
        except Exception as e:
            pytest.fail(f"Unknown breed should not raise an exception, got: {e}")

    def test_unknown_breed_retrieve_chunks_returns_empty(self):
        chunks, canonical = retrieve_chunks("Invisible Dragon Hound", "exercise?")
        assert canonical is None
        assert chunks == []

    def test_unknown_breed_recommends_vet_or_resources(self):
        answer = answer_breed_question("Transylvanian Hound", "what health problems are common?")
        answer_lower = answer.lower()
        assert "veterinarian" in answer_lower or "vet" in answer_lower or "breed association" in answer_lower, \
            "Fallback should recommend consulting a vet or breed resource"


# ---------------------------------------------------------------------------
# 3. Consistency: same question → same type of answer across runs
# ---------------------------------------------------------------------------

class TestAnswerConsistency:
    def test_golden_retriever_exercise_consistent_across_runs(self):
        q = "How much exercise does a golden retriever need daily?"
        answers = [answer_breed_question("golden retriever", q) for _ in range(3)]
        for ans in answers:
            assert "60" in ans or "90" in ans or "daily" in ans.lower(), \
                f"Inconsistent answer missing key facts: {ans[:200]}"

    def test_bulldog_exercise_consistently_low(self):
        q = "How much exercise does a bulldog need?"
        answers = [answer_breed_question("bulldog", q) for _ in range(2)]
        for ans in answers:
            assert "20" in ans or "30" in ans or "gentle" in ans.lower() or "low" in ans.lower(), \
                f"Bulldog exercise should consistently reference low intensity: {ans[:200]}"


# ---------------------------------------------------------------------------
# 4. Auto-suggested tasks match the breed profile
# ---------------------------------------------------------------------------

class TestTaskBreedAlignment:
    def test_bulldog_no_intense_long_run(self):
        tasks = suggest_tasks_for_breed("bulldog", age_years=3)
        for t in tasks:
            if t["category"] == "exercise":
                assert t["duration_minutes"] <= 40, \
                    f"Bulldog exercise task too long: {t['title']} = {t['duration_minutes']} min"
                assert "intense" not in t["title"].lower() and "run" not in t["title"].lower(), \
                    f"Bulldog should not have intense run tasks: {t['title']}"

    def test_german_shepherd_has_substantial_exercise(self):
        tasks = suggest_tasks_for_breed("german shepherd", age_years=3)
        exercise_tasks = [t for t in tasks if t["category"] == "exercise"]
        assert len(exercise_tasks) >= 1, "German Shepherd should have at least one exercise task"
        total_exercise = sum(t["duration_minutes"] for t in exercise_tasks)
        assert total_exercise >= 45, \
            f"German Shepherd total exercise should be substantial, got {total_exercise} min"

    def test_puppy_golden_gets_reduced_exercise(self):
        puppy_tasks = suggest_tasks_for_breed("golden retriever", age_years=0.5)
        adult_tasks = suggest_tasks_for_breed("golden retriever", age_years=3)
        puppy_exercise = [t for t in puppy_tasks if t["category"] == "exercise"]
        adult_exercise = [t for t in adult_tasks if t["category"] == "exercise"]
        if puppy_exercise and adult_exercise:
            puppy_total = sum(t["duration_minutes"] for t in puppy_exercise)
            adult_total = sum(t["duration_minutes"] for t in adult_exercise)
            assert puppy_total <= adult_total, \
                f"Puppy exercise ({puppy_total} min) should not exceed adult ({adult_total} min)"

    def test_persian_cat_has_grooming_task(self):
        tasks = suggest_tasks_for_breed("persian", age_years=2)
        grooming = [t for t in tasks if t["category"] == "grooming"]
        assert len(grooming) >= 1, "Persian should have at least one grooming task"

    def test_french_bulldog_has_fold_cleaning(self):
        tasks = suggest_tasks_for_breed("french bulldog", age_years=2)
        hygiene = [t for t in tasks if t["category"] == "hygiene"]
        assert any("fold" in t["title"].lower() or "facial" in t["title"].lower() for t in hygiene), \
            "French Bulldog should have facial fold cleaning task"

    def test_tasks_convert_to_Task_objects(self):
        suggestions = suggest_tasks_for_breed("corgi", age_years=4)
        task_objects = tasks_to_Task_objects(suggestions)
        assert len(task_objects) >= 1
        for task in task_objects:
            assert hasattr(task, "title")
            assert hasattr(task, "category")
            assert hasattr(task, "duration_minutes")
            assert 1 <= task.priority <= 5

    def test_feeding_tasks_included_for_all_breeds(self):
        for breed in ["golden retriever", "bulldog", "siamese", "corgi"]:
            tasks = suggest_tasks_for_breed(breed, age_years=3)
            feeding = [t for t in tasks if t["category"] == "feeding"]
            assert len(feeding) >= 1, f"{breed} should have at least one feeding task"


# ---------------------------------------------------------------------------
# 5. Guardrails: refuse vet diagnoses, recommend vet for medical emergencies
# ---------------------------------------------------------------------------

class TestGuardrails:
    def test_emergency_query_is_detected(self):
        assert _is_medical_emergency_query("can you diagnose my dog?")
        assert _is_medical_emergency_query("my dog is dying, what medication should I give?")
        assert _is_medical_emergency_query("prescribe something for my cat")

    def test_non_emergency_not_flagged(self):
        assert not _is_medical_emergency_query("how much exercise does my corgi need?")
        assert not _is_medical_emergency_query("what should I feed a golden retriever?")

    def test_diagnosis_request_refused(self):
        answer = answer_breed_question("golden retriever", "can you diagnose my dog's limp?")
        answer_lower = answer.lower()
        assert "not able to provide" in answer_lower or "cannot diagnose" in answer_lower or \
               "veterinarian" in answer_lower or "vet" in answer_lower, \
            "System should refuse to provide diagnosis"
        assert "diagnos" not in answer_lower.replace("cannot diagnose", "").replace("not able to provide veterinary diagnose", ""), \
            "System should not attempt to diagnose"

    def test_health_warning_answer_includes_vet_disclaimer(self):
        answer = answer_breed_question("german shepherd", "what are warning signs of illness?")
        assert "veterinarian" in answer.lower() or "vet" in answer.lower() or "Important" in answer, \
            "Health-related answer should mention consulting a vet"

    def test_emergency_answer_recommends_vet(self):
        answer = answer_breed_question("beagle", "my dog is having a seizure what medication should I give?")
        assert "veterinarian" in answer.lower() or "emergency" in answer.lower() or "hospital" in answer.lower(), \
            "Emergency query should direct user to veterinarian"

    def test_supported_breeds_list_returns_items(self):
        breeds = list_supported_breeds()
        assert len(breeds) >= 10, "Should have at least 10 supported breeds"
        assert any("Golden" in b for b in breeds)
        assert any("Bulldog" in b for b in breeds)
