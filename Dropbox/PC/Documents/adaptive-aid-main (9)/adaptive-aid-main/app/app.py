import os
import shutil
from datetime import datetime, timezone

from app.routes.auth import router as auth_router
from app.routes.courses import router as courses_router
from app.routes.materials import router as materials_router
from app.routes.session import router as session_router 
from app.routes.questions import router as questions_router
from app.routes.analytics import router as analytics_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from app.db import create_db_and_tables, get_session
from app.models import (
    Student,
    Course,
    CourseMaterial,
    Quiz,
    QuizMaterial,
    Question,
    QuestionOptions,
    Response,
    Report,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/progress/{student_id}")
def get_progress(student_id: int, session: Session = Depends(get_session)):
    quizzes = session.exec(
        select(Quiz).where(Quiz.student_id == student_id)
    ).all()

    quiz_ids = [q.id for q in quizzes]

    reports = []
    for qid in quiz_ids:
        rep = session.exec(select(Report).where(Report.quiz_id == qid)).first()
        if rep:
            reports.append(rep)

    total_quizzes = len(quizzes)
    total_reports = len(reports)

    correct_count = 0
    for rep in reports:
        if rep.summary_json and rep.summary_json.get("is_correct") is True:
            correct_count += 1

    average_score = (correct_count / total_reports * 100) if total_reports > 0 else 0

    return {
        "student_id": student_id,
        "total_quizzes": total_quizzes,
        "reports_generated": total_reports,
        "correct_answers": correct_count,
        "average_score_percentage": average_score
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(materials_router)
app.include_router(session_router)
app.include_router(questions_router)
app.include_router(analytics_router)

