from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Course, Quiz, Report, CourseMaterial

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_score_percent(report: Report) -> float:
    summary = report.summary_json or {}

    if "overall_performance" in summary:
        return float(summary["overall_performance"].get("score_percent", 0))

    return float(summary.get("score_percent", 0))


def get_score_text(report: Report) -> str:
    summary = report.summary_json or {}

    if "overall_performance" in summary:
        return summary["overall_performance"].get("score_text", "0/0")

    total_correct = summary.get("total_correct", 0)
    total_answered = summary.get("total_answered", 0)
    return f"{total_correct}/{total_answered}"


@router.get("/student/{student_id}/courses")
def get_student_course_analytics(
    student_id: int,
    session: Session = Depends(get_session)
):
    courses = session.exec(select(Course)).all()

    result = []

    for course in courses:
        quizzes = session.exec(
            select(Quiz).where(
                Quiz.student_id == student_id,
                Quiz.course_id == course.id
            )
        ).all()

        quiz_ids = [q.id for q in quizzes]

        reports = []

        if quiz_ids:
            reports = session.exec(
                select(Report).where(Report.quiz_id.in_(quiz_ids))
            ).all()

        scores = [get_score_percent(report) for report in reports]

        average_score = round(sum(scores) / len(scores), 1) if scores else 0
        highest_score = round(max(scores), 1) if scores else 0
        sessions_completed = len(reports)

        last_report = None
        if reports:
            last_report = max(reports, key=lambda r: r.created_at)

        result.append({
            "course_id": course.id,
            "course_name": getattr(course, "course_name", None) or getattr(course, "name", None) or f"Course {course.id}",
            "average_score": average_score,
            "highest_score": highest_score,
            "sessions_completed": sessions_completed,
            "last_session_date": last_report.created_at.isoformat() if last_report else None        
        })

    return {
        "student_id": student_id,
        "courses": result
    }


@router.get("/student/{student_id}/course/{course_id}/reports")
def get_course_report_history(
    student_id: int,
    course_id: int,
    session: Session = Depends(get_session)
):
    course = session.get(Course, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    quizzes = session.exec(
        select(Quiz).where(
            Quiz.student_id == student_id,
            Quiz.course_id == course_id
        )
    ).all()

    quiz_ids = [q.id for q in quizzes]

    if not quiz_ids:
        return {
            "student_id": student_id,
            "course_id": course_id,
            "course_name": getattr(course, "course_name", None) or getattr(course, "name", None) or f"Course {course.id}",
            "reports": []
        }

    reports = session.exec(
        select(Report).where(Report.quiz_id.in_(quiz_ids))
    ).all()

    reports = sorted(reports, key=lambda r: r.created_at, reverse=True)

    result = []

    for report in reports:
        summary = report.summary_json or {}

        quiz = session.get(Quiz, report.quiz_id)
        material_name = "Unknown material"

        if quiz and quiz.course_material_id:
            material = session.get(CourseMaterial, quiz.course_material_id)
            if material:
                material_name = material.filename

        result.append({
            "report_id": report.id,
            "quiz_id": report.quiz_id,
            "created_at": report.created_at.isoformat(),
            "material_name": material_name,
            "score_text": get_score_text(report),
            "score_percent": get_score_percent(report),
            "summary": summary
        })

    return {
        "student_id": student_id,
        "course_id": course_id,
        "course_name": getattr(course, "course_name", None) or getattr(course, "name", None) or f"Course {course.id}",
        "reports": result
    }