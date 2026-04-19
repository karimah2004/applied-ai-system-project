"""
RAG engine for PawPal+: retrieves breed-specific knowledge and grounds
LLM answers in retrieved context using the Anthropic Claude API.
"""

import os
import re
import math
from pathlib import Path
from collections import Counter

import anthropic

KNOWLEDGE_DIR = Path(__file__).parent / "breed_knowledge"

BREED_FILE_MAP: dict[str, str] = {
    "golden retriever": "golden_retriever.md",
    "golden": "golden_retriever.md",
    "labrador retriever": "labrador_retriever.md",
    "labrador": "labrador_retriever.md",
    "lab": "labrador_retriever.md",
    "french bulldog": "french_bulldog.md",
    "frenchie": "french_bulldog.md",
    "bulldog": "bulldog.md",
    "english bulldog": "bulldog.md",
    "corgi": "corgi.md",
    "pembroke welsh corgi": "corgi.md",
    "poodle": "poodle.md",
    "standard poodle": "poodle.md",
    "german shepherd": "german_shepherd.md",
    "gsd": "german_shepherd.md",
    "beagle": "beagle.md",
    "maine coon": "maine_coon.md",
    "siamese": "siamese.md",
    "persian": "persian.md",
    "yorkshire terrier": "yorkshire_terrier.md",
    "yorkie": "yorkshire_terrier.md",
    "shih tzu": "shih_tzu.md",
    "bengal": "bengal.md",
    "bengal cat": "bengal.md",
}

SECTION_HEADERS = [
    "Exercise Needs",
    "Common Health Issues",
    "Dietary Guidelines",
    "Grooming Requirements",
    "Temperament and Training Notes",
    "Age-Specific Care",
]

MEDICAL_DISCLAIMER = (
    "⚠️ **Important:** PawPal+ provides general breed guidance only. "
    "It cannot diagnose medical conditions or replace professional veterinary advice. "
    "If your pet shows signs of illness, injury, or distress, please contact your veterinarian immediately."
)

EMERGENCY_KEYWORDS = {
    "diagnose", "diagnosis", "prescribed", "prescription", "medication dosage",
    "treat my dog", "treat my cat", "cure", "my dog is dying", "my cat is dying",
    "emergency", "poisoned", "overdose",
}


def _resolve_breed(breed_name: str) -> tuple[str | None, str | None]:
    """Return (canonical_name, file_path) or (None, None) if not found."""
    key = breed_name.strip().lower()
    filename = BREED_FILE_MAP.get(key)
    if not filename:
        for alias, fname in BREED_FILE_MAP.items():
            if key in alias or alias in key:
                filename = fname
                break
    if not filename:
        return None, None
    file_path = KNOWLEDGE_DIR / filename
    if not file_path.exists():
        return None, None
    canonical = filename.replace(".md", "").replace("_", " ").title()
    return canonical, str(file_path)


def _load_sections(file_path: str) -> dict[str, str]:
    """Parse a breed markdown file into section_name → content dict."""
    text = Path(file_path).read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current_header = "__intro__"
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z]+\b", text.lower())


def _tfidf_score(query_tokens: list[str], section_text: str, all_sections: list[str]) -> float:
    """Compute a simple TF-IDF relevance score for a section."""
    doc_tokens = _tokenize(section_text)
    if not doc_tokens:
        return 0.0
    doc_freq = Counter(doc_tokens)
    doc_len = len(doc_tokens)

    score = 0.0
    N = len(all_sections)
    for token in set(query_tokens):
        tf = doc_freq.get(token, 0) / doc_len
        df = sum(1 for s in all_sections if token in _tokenize(s))
        idf = math.log((N + 1) / (df + 1)) + 1
        score += tf * idf
    return score


def retrieve_chunks(breed_name: str, question: str, top_k: int = 3) -> tuple[list[str], str | None]:
    """
    Retrieve the most relevant sections from the breed knowledge base.

    Returns:
        (chunks, canonical_name) — chunks is a list of section strings,
        canonical_name is None if breed not found.
    """
    canonical, file_path = _resolve_breed(breed_name)
    if not canonical or not file_path:
        return [], None

    sections = _load_sections(file_path)
    all_texts = list(sections.values())
    query_tokens = _tokenize(question)

    scored = [
        (header, text, _tfidf_score(query_tokens, text, all_texts))
        for header, text in sections.items()
        if header != "__intro__"
    ]
    scored.sort(key=lambda x: x[2], reverse=True)

    chunks = [f"**{hdr}**\n{txt}" for hdr, txt, _ in scored[:top_k]]
    return chunks, canonical


def _is_medical_emergency_query(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in EMERGENCY_KEYWORDS)


def answer_breed_question(breed_name: str, question: str) -> str:
    """
    Main RAG entry point: retrieve breed context and generate a grounded answer.

    Returns a string answer (with source citations and vet disclaimer when relevant).
    """
    if _is_medical_emergency_query(question):
        return (
            "I'm not able to provide veterinary diagnoses or prescribe treatments. "
            "Please contact your veterinarian or an emergency animal hospital immediately.\n\n"
            + MEDICAL_DISCLAIMER
        )

    chunks, canonical = retrieve_chunks(breed_name, question)

    if not canonical:
        return _fallback_answer(breed_name, question)

    context = "\n\n---\n\n".join(chunks)

    system_prompt = (
        "You are PawPal+, a knowledgeable pet care assistant. "
        "Answer the user's question using ONLY the breed-specific context provided below. "
        "Be specific and reference details from the context. "
        "If the context does not fully answer the question, say so clearly and suggest consulting a vet. "
        "Do NOT fabricate breed information not present in the context. "
        "Never provide veterinary diagnoses or medication prescriptions."
    )

    user_prompt = (
        f"Breed: {canonical}\n\n"
        f"Retrieved breed context:\n{context}\n\n"
        f"User question: {question}"
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    answer = response.content[0].text

    cited_headers = [line.replace("**", "").replace(":", "").strip()
                     for line in context.splitlines() if line.startswith("**")]
    citation = f"\n\n*Sources: {', '.join(cited_headers[:3])} — {canonical} breed profile*"

    health_keywords = {"health", "sick", "symptom", "pain", "limp", "vomit", "emergency", "warning"}
    if any(kw in question.lower() for kw in health_keywords):
        return answer + citation + "\n\n" + MEDICAL_DISCLAIMER

    return answer + citation


def _fallback_answer(breed_name: str, question: str) -> str:
    """Generate a general answer when breed is not in knowledge base."""
    system_prompt = (
        "You are PawPal+, a pet care assistant. "
        "The user asked about a breed that is not in our knowledge base. "
        "Acknowledge this gap clearly, then provide general pet care advice. "
        "Be honest that your answer is general, not breed-specific. "
        "Recommend consulting a veterinarian or breed-specific resources."
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": (
                f"I don't have specific information about the '{breed_name}' breed in my knowledge base. "
                f"The user asked: {question}"
            )
        }],
    )

    answer = response.content[0].text
    return (
        f"⚠️ **'{breed_name}' is not in our breed database yet.**\n\n"
        + answer
        + "\n\n*For breed-specific guidance, please consult your veterinarian or a reputable breed association.*"
    )


def list_supported_breeds() -> list[str]:
    """Return a sorted list of supported breed names."""
    seen_files: set[str] = set()
    breeds: list[str] = []
    for alias, fname in BREED_FILE_MAP.items():
        if fname not in seen_files:
            seen_files.add(fname)
            breeds.append(alias.title())
    return sorted(breeds)
