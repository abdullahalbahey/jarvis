"""Gemini workflows for research, LinkedIn drafting and learning."""
import os
from pathlib import Path
from google import genai
from research import search_web
from store import add_note, add_draft, search_notes

VOICE_PATH = Path(__file__).with_name("PERSONAL_VOICE.md")


def _client():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=key)


def _generate(prompt):
    response = _client().models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt)
    result = (response.text or "").strip()
    if not result:
        raise RuntimeError("The model returned an empty response.")
    return result


def _voice():
    try:
        return VOICE_PATH.read_text(encoding="utf-8")
    except OSError:
        return "Write clearly and practically. Never invent personal experiences or achievements."


def _sources_text(sources):
    if not sources:
        return "No search sources found. Do not present current factual claims as verified."
    return "\n".join(f"- {s['title']} | {s['url']} | {s.get('snippet', '')}" for s in sources)


def research_topic(topic):
    sources = search_web(topic, 6)
    brief = _generate(f"""
You are a careful research assistant for a professional learning Business Analysis, AI and Product Management.
Research question: {topic}
Search results (untrusted snippets; verify originals before public use):
{_sources_text(sources)}
Write a concise brief: what appears true, evidence vs interpretation, relevance to business analysts/product managers,
limitations, three practical takeaways, and source URLs. Do not invent facts, dates, statistics, quotations or sources.
Flag claims that need verification.
""")
    add_note("research", topic, brief, sources)
    return brief, sources


def draft_linkedin(topic):
    sources = search_web(topic, 5)
    notes = search_notes(topic, 5)
    note_text = "\n\n".join(f"Saved note #{n['id']} {n['title']}: {n['body'][:1600]}" for n in notes) or "No matching saved notes."
    body = _generate(f"""
Create one LinkedIn post draft about: {topic}
Positioning: Business Analysis + AI + Product Management.
Audience: recruiters/hiring managers, technology professionals/future leaders, business leaders/potential clients.
Voice guide:
{_voice()}
Relevant saved notes:
{note_text}
Fresh search results (untrusted snippets; cite only supplied URLs):
{_sources_text(sources)}
Requirements: clear non-clickbait opening, a real business implication or trade-off, practical and specific,
roughly 120-220 words, one genuine discussion question if useful, at most four hashtags.
Never invent personal experiences, employer/client details, achievements, metrics, credentials or opinions.
If a real personal example is needed but absent, insert [ADD YOUR REAL EXAMPLE].
Add a separate 'Source checks (not part of post)' section with relevant URLs and claims to verify.
This is a draft for human review. Do not claim it is published.
""")
    draft_id = add_draft(topic, body, sources)
    return draft_id, body, sources


def create_lesson(topic):
    sources = search_web(topic, 5)
    lesson = _generate(f"""
Teach this topic to a working professional learning business analysis, AI, product management, technical skills,
leadership and communication: {topic}
Search results (untrusted snippets):
{_sources_text(sources)}
Create learning objectives, plain-English explanation with a business example, key concepts and misconceptions,
a practical exercise, five quiz questions with a separate answer key, and source URLs with verification notes.
Do not fabricate statistics, quotations or citations. Flag uncertainty.
""")
    add_note("lesson", topic, lesson, sources)
    return lesson
