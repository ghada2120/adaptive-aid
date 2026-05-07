import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

def read_text_from_txt_file(txt_file_path: str) -> str:
    path = Path(txt_file_path)

    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {txt_file_path}")

    text = path.read_text(encoding="utf-8", errors="ignore").strip()

    if not text:
        raise ValueError("Extracted text file is empty")

    return text


def generate_mcq_bank_from_material(
    material_text: str,
    difficulty_level: int,
    count: int = 3,
    excluded_questions: list[str] | None = None
) -> dict:
    if not material_text or not material_text.strip():
        raise ValueError("material_text is empty")

    if difficulty_level not in [1, 2, 3]:
        raise ValueError("difficulty_level must be 1, 2, or 3")

    material_text = material_text[:4000]
    excluded_questions = excluded_questions or []

    excluded_text = "\n".join([f"- {q}" for q in excluded_questions[:20]])

    prompt = f"""
You are generating quiz questions for a learning system.

Return json only.
Do not use markdown.
Do not add any explanation outside the json.

Generate exactly {count} multiple-choice questions based only on the material below.

Rules:
- every question must have difficulty_level = {difficulty_level}
- each question must have exactly 4 options
- exactly 1 option must have "is_correct": true
- the other 3 options must have "is_correct": false
- questions must be clear and not vague
- options must not be duplicates
- do not invent facts outside the material
- do not repeat or closely paraphrase any previously generated question
- each question must include "topic"
- each question must include "subtopic"
- topic should be the broad subject area from the material
- subtopic should be the specific concept being tested

Difficulty meaning:
- difficulty_level 1 = easy: direct recall, simple facts, obvious answers
- difficulty_level 2 = medium: requires understanding, comparison, or applying concepts
- difficulty_level 3 = hard: requires deeper reasoning, tricky distinctions, multi-step understanding, or inference from the material

Previously generated questions to avoid:
{excluded_text if excluded_text else "None"}

Return this exact json shape:

{{
  "questions": [
    {{
      "question_text": "string",
      "difficulty_level": {difficulty_level},
      "topic": "main topic from the material",
      "subtopic": "specific subtopic tested by this question",
      "options": [
        {{"option_text": "string", "is_correct": false}},
        {{"option_text": "string", "is_correct": true}},
        {{"option_text": "string", "is_correct": false}},
        {{"option_text": "string", "is_correct": false}}
      ]
    }}
  ]
}}

Material:
\"\"\"{material_text}\"\"\"
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": "You output valid json only."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")


def generate_mcq_bank_from_txt(
    txt_file_path: str,
    difficulty_level: int,
    count: int = 3,
    excluded_questions: list[str] | None = None
) -> dict:
    material_text = read_text_from_txt_file(txt_file_path)
    return generate_mcq_bank_from_material(
        material_text=material_text,
        difficulty_level=difficulty_level,
        count=count,
        excluded_questions=excluded_questions
    )