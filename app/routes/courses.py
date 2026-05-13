from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Course, Student, CourseMaterial, Quiz, Question, QuestionOptions, Response, Report
from app.schemas import CreateCourseRequest, RenameCourseRequest

from pathlib import Path
router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("/")
def create_course(data: CreateCourseRequest, session: Session = Depends(get_session)):
    student = session.get(Student, data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    course = Course(
        name=data.course_name,
        student_id=data.student_id
    )

    session.add(course)
    session.commit()
    session.refresh(course)

    return {
        "message": "Course created successfully",
        "course_id": course.id,
        "course_name": course.name
    }


@router.get("/{student_id}")
def list_courses(student_id: int, session: Session = Depends(get_session)):
    courses = session.exec(
        select(Course).where(Course.student_id == student_id)
    ).all()

    return {
        "student_id": student_id,
        "courses": [
            {"id": c.id, "name": c.name}
            for c in courses
        ]
    }

@router.delete("/{course_id}")
def delete_course(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    materials = session.exec(
        select(CourseMaterial).where(CourseMaterial.course_id == course_id)
    ).all()

    for material in materials:
        if material.file_path:
            file_path = Path(material.file_path)
            if file_path.exists():
                file_path.unlink()

        session.delete(material)

    quizzes = session.exec(
        select(Quiz).where(Quiz.course_id == course_id)
    ).all()

    for quiz in quizzes:
        reports = session.exec(
            select(Report).where(Report.quiz_id == quiz.id)
        ).all()

        for report in reports:
            session.delete(report)

        questions = session.exec(
            select(Question).where(Question.quiz_id == quiz.id)
        ).all()

        for question in questions:
            responses = session.exec(
                select(Response).where(Response.question_id == question.id)
            ).all()

            for response in responses:
                session.delete(response)

            options = session.exec(
                select(QuestionOptions).where(QuestionOptions.question_id == question.id)
            ).all()

            for option in options:
                session.delete(option)

            session.delete(question)

        session.delete(quiz)

    session.delete(course)
    session.commit()

    return {
        "message": "Course deleted successfully",
        "course_id": course_id
    }

@router.put("/{course_id}")
def rename_course(
    course_id: int,
    data: RenameCourseRequest,
    session: Session = Depends(get_session)
):
    course = session.get(Course, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    new_name = data.course_name.strip()

    if not new_name:
        raise HTTPException(status_code=400, detail="Course name cannot be empty")

    course.name = new_name

    session.add(course)
    session.commit()
    session.refresh(course)

    return {
        "message": "Course renamed successfully",
        "course_id": course.id,
        "course_name": course.name
    }