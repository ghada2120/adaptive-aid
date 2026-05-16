def validate_generated_question(question: dict) -> tuple[bool, str]:
    required_fields = ["question_text", "difficulty_level", "topic", "subtopic", "options"]

    for field in required_fields:
        if field not in question:
            return False, f"Missing field: {field}"

    question_text = question["question_text"]
    difficulty_level = question["difficulty_level"]
    topic = question["topic"]
    subtopic = question["subtopic"]
    options = question["options"]

    if not isinstance(question_text, str) or not question_text.strip():
        return False, "question_text is empty or invalid"

    if not isinstance(difficulty_level, int):
        return False, "difficulty_level must be an integer"

    if difficulty_level not in [1, 2, 3]:
        return False, "difficulty_level must be 1, 2, or 3"

    if not isinstance(topic, str) or not topic.strip():
        return False, "topic is empty or invalid"

    if not isinstance(subtopic, str) or not subtopic.strip():
        return False, "subtopic is empty or invalid"

    if not isinstance(options, list) or len(options) != 4:
        return False, "Each question must have exactly 4 options"

    seen_texts = set()
    correct_count = 0

    for option in options:
        if not isinstance(option, dict):
            return False, "Each option must be an object"

        if "option_text" not in option or "is_correct" not in option:
            return False, "Each option must contain option_text and is_correct"

        option_text = option["option_text"]
        is_correct = option["is_correct"]

        if not isinstance(option_text, str) or not option_text.strip():
            return False, "Option text is empty or invalid"

        normalized = option_text.strip().lower()

        if normalized in seen_texts:
            return False, "Duplicate option texts found"

        seen_texts.add(normalized)

        if not isinstance(is_correct, bool):
            return False, "is_correct must be boolean"

        if is_correct:
            correct_count += 1

    if correct_count != 1:
        return False, "There must be exactly one correct option"

    return True, "Valid"


def validate_generated_questions_payload(payload: dict) -> tuple[bool, list[dict], list[str]]:
    if not isinstance(payload, dict):
        return False, [], ["Payload must be an object"]

    if "questions" not in payload:
        return False, [], ["Missing 'questions' key"]

    questions = payload["questions"]

    if not isinstance(questions, list) or not questions:
        return False, [], ["'questions' must be a non-empty list"]

    valid_questions = []
    errors = []

    for idx, question in enumerate(questions, start=1):
        is_valid, message = validate_generated_question(question)

        if is_valid:
            cleaned_question = {
                "question_text": question["question_text"].strip(),
                "difficulty_level": question["difficulty_level"],
                "topic": question["topic"].strip(),
                "subtopic": question["subtopic"].strip(),
                "options": question["options"]
            }

            valid_questions.append(cleaned_question)
        else:
            errors.append(f"Question {idx}: {message}")

    return len(valid_questions) > 0, valid_questions, errors