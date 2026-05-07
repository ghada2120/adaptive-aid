from sqlmodel import SQLModel, Field
from sqlalchemy import Column 
from sqlalchemy.types import JSON
from typing import Optional
from datetime import datetime, timezone 


class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str 
    email: str = Field(sa_column_kwargs={"unique": True}, index=True)
    hash_pwd : str 
    is_email_verified: bool = Field(default=False)
    verification_token: str | None = Field(default=None)
    reset_token: str | None = None
    reset_token_expires: datetime | None = None

class Course(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    student_id: int = Field(foreign_key= "student.id")

class CourseMaterial(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    filename: str
    file_path: str

class Quiz(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    course_id: int = Field(foreign_key="course.id")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = Field(default=None)
    course_material_id: int | None = Field(default=None, foreign_key="coursematerial.id")
    
class QuizMaterial(SQLModel, table=True):
    quiz_id: int = Field(foreign_key="quiz.id", primary_key=True)
    course_material_id: int = Field(foreign_key="coursematerial.id", primary_key=True)

class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question_no: int
    difficulty_level: int
    question_text: str
    quiz_id: int =Field(foreign_key = "quiz.id")
    topic: str | None = None
    subtopic: str | None = None

class QuestionOptions(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    option_text: str
    is_correct: bool | None = None 
    

class Response(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    selected_option: int | None = None
    is_correct: bool | None = None   
    is_skipped: bool = False
    answered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Report(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    quiz_id : int =Field(foreign_key = "quiz.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # score calculated when displaying eval report
    summary_json: dict | None  = Field(
    default=None,
    sa_column=Column(JSON)
)
    

