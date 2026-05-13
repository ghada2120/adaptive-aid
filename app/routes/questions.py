from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    Student,
    Course,
    Quiz,
    Question,
    QuestionOptions,
    Response,
    CourseMaterial,
)
from app.schemas import SubmitAnswerRequest
from app.services.ai_service import generate_mcq_bank_from_material
from app.services.validation_service import validate_generated_questions_payload
from app.services.material_service import extract_text_from_material

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/generate-from-material")
def generate_questions_from_material(
    student_id: int,
    course_id: int,
    course_material_id: int,
    session: Session = Depends(get_session)
):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    material = session.get(CourseMaterial, course_material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Course material not found")

    try:
        material_text = extract_text_from_material(material.file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {str(e)}")

    if not material_text.strip():
        raise HTTPException(status_code=400, detail="Extracted material text is empty")

    quiz = Quiz(
    student_id=student_id,
    course_id=course_id,
    course_material_id=course_material_id
)
    session.add(quiz)
    session.commit()
    session.refresh(quiz)

    all_valid_questions = []
    all_errors = []

    for difficulty_level in [1, 2, 3]:
        try:
            payload = generate_mcq_bank_from_material(
                material_text=material_text,
                difficulty_level=difficulty_level,
                count=5
            )

            print("DIFFICULTY:", difficulty_level)
            print("AI RAW COUNT:", len(payload.get("questions", [])))
            print("AI RAW PAYLOAD:", payload)

            is_valid, valid_questions, errors = validate_generated_questions_payload(payload)

            print("VALID COUNT:", len(valid_questions))
            print("VALIDATION ERRORS:", errors)

            all_valid_questions.extend(valid_questions)
            all_errors.extend(errors)

        except Exception as e:
            all_errors.append(f"Difficulty {difficulty_level}: {str(e)}")

    if not all_valid_questions:
        raise HTTPException(
            status_code=500,
            detail=f"No valid questions generated. Errors: {all_errors}"
        )

    created_questions = []
    question_no_counter = 1

    for q_data in all_valid_questions:
        question = Question(
            question_no=question_no_counter,
            difficulty_level=q_data["difficulty_level"],
            question_text=q_data["question_text"],
            topic=q_data.get("topic"),
            subtopic=q_data.get("subtopic"),
            quiz_id=quiz.id
        )

        session.add(question)
        session.commit()
        session.refresh(question)

        for op_data in q_data["options"]:
            option = QuestionOptions(
                question_id=question.id,
                option_text=op_data["option_text"],
                is_correct=op_data["is_correct"]
            )
            session.add(option)

        session.commit()

        created_questions.append({
            "question_id": question.id,
            "question_no": question.question_no,
            "difficulty_level": question.difficulty_level,
            "topic": question.topic,
            "subtopic": question.subtopic,
            "question_text": question.question_text
        })

        question_no_counter += 1

    return {
        "message": "AI question bank created successfully",
        "quiz_id": quiz.id,
        "course_material_id": course_material_id,
        "total_questions": len(created_questions),
        "questions": created_questions,
        "validation_errors": all_errors
    }


@router.get("/quiz/{quiz_id}")
def get_questions_by_quiz(quiz_id: int, session: Session = Depends(get_session)):
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = session.exec(
        select(Question).where(Question.quiz_id == quiz_id)
    ).all()

    result = []

    for q in questions:
        options = session.exec(
            select(QuestionOptions).where(QuestionOptions.question_id == q.id)
        ).all()

        result.append({
            "id": q.id,
            "question_no": q.question_no,
            "difficulty_level": q.difficulty_level,
            "question_text": q.question_text,
            "options": [
                {
                    "id": op.id,
                    "option_text": op.option_text
                }
                for op in options
            ]
        })

    return {
        "quiz_id": quiz_id,
        "questions": result
    }


@router.post("/submit")
def submit_answer(data: SubmitAnswerRequest, session: Session = Depends(get_session)):
    question = session.get(Question, data.question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    correct_option = session.exec(
        select(QuestionOptions).where(
            QuestionOptions.question_id == data.question_id,
            QuestionOptions.is_correct == True
        )
    ).first()

    if not correct_option:
        raise HTTPException(status_code=500, detail="Correct option not found for this question")

    if data.is_skipped:
        response = Response(
            question_id=data.question_id,
            selected_option=None,
            is_correct=None,
            is_skipped=True
        )

        session.add(response)
        session.commit()
        session.refresh(response)

        return {
            "message": "Question skipped",
            "response_id": response.id,
            "question_id": data.question_id,
            "selected_option_id": None,
            "is_correct": None,
            "is_skipped": True,
            "correct_option_id": correct_option.id,
            "correct_option_text": correct_option.option_text
        }

    if data.selected_option_id is None:
        raise HTTPException(status_code=400, detail="selected_option_id is required")

    selected_option = session.get(QuestionOptions, data.selected_option_id)

    if not selected_option:
        raise HTTPException(status_code=404, detail="Option not found")

    if selected_option.question_id != data.question_id:
        raise HTTPException(status_code=400, detail="Option does not belong to this question")

    response = Response(
        question_id=data.question_id,
        selected_option=data.selected_option_id,
        is_correct=selected_option.is_correct,
        is_skipped=False
    )

    session.add(response)
    session.commit()
    session.refresh(response)

    return {
        "message": "Answer submitted successfully",
        "response_id": response.id,
        "question_id": data.question_id,
        "selected_option_id": data.selected_option_id,
        "is_correct": selected_option.is_correct,
        "is_skipped": False,
        "correct_option_id": correct_option.id,
        "correct_option_text": correct_option.option_text
    }

@router.get("/next/{quiz_id}")
def get_next_question(quiz_id: int, session: Session = Depends(get_session)):
    quiz = session.get(Quiz, quiz_id)

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = session.exec(
        select(Question).where(Question.quiz_id == quiz_id)
    ).all()

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this quiz")

    question_ids = [q.id for q in questions]

    responses = session.exec(
        select(Response)
        .where(Response.question_id.in_(question_ids))
        .order_by(Response.answered_at)
    ).all()

    answered_question_ids = {r.question_id for r in responses}

    def format_question(q: Question):
        options = session.exec(
            select(QuestionOptions).where(QuestionOptions.question_id == q.id)
        ).all()

        return {
            "question_id": q.id,
            "question_no": q.question_no,
            "question_text": q.question_text,
            "difficulty_level": q.difficulty_level,
            "topic": q.topic,
            "subtopic": q.subtopic,
            "options": [
                {
                    "id": op.id,
                    "option_text": op.option_text
                }
                for op in options
            ]
        }

    def get_unanswered_question_by_difficulty(difficulty_level: int):
        updated_questions = session.exec(
            select(Question).where(
                Question.quiz_id == quiz_id,
                Question.difficulty_level == difficulty_level
            )
        ).all()

        for q in updated_questions:
            if q.id not in answered_question_ids:
                return q

        return None

    def get_existing_question_texts_for_difficulty(difficulty_level: int):
        existing_texts = session.exec(
            select(Question.question_text).where(
                Question.quiz_id == quiz_id,
                Question.difficulty_level == difficulty_level
            )
        ).all()

        return list(existing_texts)

    def generate_more_questions_for_difficulty(difficulty_level: int, count: int = 5):
        if not quiz.course_material_id:
            raise HTTPException(
                status_code=400,
                detail="Quiz is missing course material ID. Cannot generate more questions."
            )

        material = session.get(CourseMaterial, quiz.course_material_id)

        if not material:
            raise HTTPException(status_code=404, detail="Course material not found")

        try:
            material_text = extract_text_from_material(material.file_path)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from material: {str(e)}"
            )

        if not material_text.strip():
            raise HTTPException(status_code=400, detail="Extracted material text is empty")

        excluded_questions = get_existing_question_texts_for_difficulty(difficulty_level)

        try:
            payload = generate_mcq_bank_from_material(
                material_text=material_text,
                difficulty_level=difficulty_level,
                count=count,
                excluded_questions=excluded_questions
            )

            is_valid, valid_questions, errors = validate_generated_questions_payload(payload)

            if not is_valid or not valid_questions:
                raise HTTPException(
                    status_code=500,
                    detail=f"AI did not generate valid questions. Errors: {errors}"
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate more questions: {str(e)}"
            )

        current_max_question_no = session.exec(
            select(Question.question_no).where(Question.quiz_id == quiz_id)
        ).all()

        next_question_no = max(current_max_question_no) + 1 if current_max_question_no else 1

        created_questions = []

        for q_data in valid_questions:
            question = Question(
                question_no=next_question_no,
                difficulty_level=q_data["difficulty_level"],
                question_text=q_data["question_text"],
                topic=q_data.get("topic"),
                subtopic=q_data.get("subtopic"),
                quiz_id=quiz.id
            )

            session.add(question)
            session.commit()
            session.refresh(question)

            for op_data in q_data["options"]:
                option = QuestionOptions(
                    question_id=question.id,
                    option_text=op_data["option_text"],
                    is_correct=op_data["is_correct"]
                )
                session.add(option)

            session.commit()

            created_questions.append(question)
            next_question_no += 1

        return created_questions

    # First question starts at medium
    if not responses:
        target_difficulty = 2
    else:
        last_response = responses[-1]
        last_question = session.get(Question, last_response.question_id)

        if not last_question:
            raise HTTPException(status_code=404, detail="Last question not found")

        if last_response.is_skipped:
            target_difficulty = last_question.difficulty_level
        elif last_response.is_correct is True:
            target_difficulty = min(3, last_question.difficulty_level + 1)
        elif last_response.is_correct is False:
            target_difficulty = max(1, last_question.difficulty_level - 1)
        else:
            target_difficulty = last_question.difficulty_level

    q = get_unanswered_question_by_difficulty(target_difficulty)

    if q:
        result = format_question(q)
        result["debug_target_difficulty"] = target_difficulty
        result["debug_source"] = "existing_question"
        return result

    # If target difficulty is empty, generate more questions for SAME difficulty
    generate_more_questions_for_difficulty(target_difficulty, count=5)

    q = get_unanswered_question_by_difficulty(target_difficulty)

    if q:
        result = format_question(q)
        result["debug_target_difficulty"] = target_difficulty
        result["debug_source"] = "ai_replenished_question"
        return result

    return {
        "message": "Quiz completed"
    }