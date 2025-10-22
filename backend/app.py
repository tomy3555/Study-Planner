from datetime import date
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from sqlalchemy import text

from .db import get_db
from .models import Subject, Summary
from .models import StudyPlan, StudyTask
from .services.plan import generate_plan

from .schemas import (
    SubjectCreate, SubjectOut,
    SummaryCreate, SummaryOut, 
    PlanGenerateIn, StudyPlanOut, 
    StudyTaskOut, TaskPatchIn
)

app = FastAPI(title="StudyPlanner ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "*",            # en dev, más fácil
        "null"          # si abrís el index.html con file://
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Subjects ----------
@app.post("/api/subjects", response_model=SubjectOut, response_model_by_alias=True, status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(Subject).where(Subject.name == payload.name))
    if exists:
        raise HTTPException(409, "Subject name already exists")
    sub = Subject(name=payload.name)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@app.get("/api/subjects", response_model=list[SubjectOut], response_model_by_alias=True)
def list_subjects(db: Session = Depends(get_db)):
    rows = db.execute(select(Subject).order_by(Subject.id.desc())).scalars().all()
    return rows

# ---------- Summaries ----------
@app.post("/api/summaries", response_model=SummaryOut, response_model_by_alias=True, status_code=201)
def create_summary(payload: SummaryCreate, db: Session = Depends(get_db)):
    # Validaciones básicas
    subject = db.scalar(select(Subject).where(Subject.id == payload.subject_id))
    if not subject:
        raise HTTPException(404, "Subject not found")
    if payload.pages <= 0:
        raise HTTPException(422, "Pages must be > 0")

    s = Summary(
        subject_id=payload.subject_id,
        title=payload.title,
        pages=payload.pages,
        exam_date=payload.exam_date
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@app.get("/api/summaries", response_model=list[SummaryOut], response_model_by_alias=True)
def list_summaries(subject_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Summary).order_by(Summary.id.desc())
    if subject_id:
        stmt = stmt.where(Summary.subject_id == subject_id)
    rows = db.execute(stmt).scalars().all()
    return rows

@app.get("/debug/db")
def debug_db(db = Depends(get_db)):
    db.execute(text("SELECT 1"))
    count = db.execute(text("SELECT COUNT(*) FROM subjects")).scalar()
    return {"ok": True, "subjectsCount": int(count)}

@app.post("/api/plans/generate", response_model=StudyPlanOut, response_model_by_alias=True, status_code=201)
def post_generate_plan(payload: PlanGenerateIn, db: Session = Depends(get_db)):
    try:
        plan = generate_plan(
            db,
            summary_id=payload.summary_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            read_ratio=float(payload.read_ratio),
            buffer_days=payload.buffer_days,
            review_quota=payload.review_quota,
        )
        return plan
    except ValueError as e:
        raise HTTPException(400, str(e))
    
@app.get("/api/plans/{plan_id}/tasks", response_model=list[StudyTaskOut], response_model_by_alias=True)
def get_plan_tasks(
    plan_id: int,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db), 
):
    plan = db.scalar(select(StudyPlan).where(StudyPlan.id == plan_id))
    if not plan:
        raise HTTPException(404, "Plan not found")

    stmt = select(StudyTask).where(StudyTask.plan_id == plan_id).order_by(StudyTask.day_date.asc(), StudyTask.task_type.asc())
    if from_date and to_date:
        stmt = stmt.where(and_(StudyTask.day_date >= from_date, StudyTask.day_date <= to_date))
    elif from_date:
        stmt = stmt.where(StudyTask.day_date >= from_date)
    elif to_date:
        stmt = stmt.where(StudyTask.day_date <= to_date)

    return db.execute(stmt).scalars().all()

@app.patch("/api/tasks/{task_id}", response_model=StudyTaskOut, response_model_by_alias=True)
def patch_task(task_id: int, payload: TaskPatchIn, db: Session = Depends(get_db)):
    t = db.scalar(select(StudyTask).where(StudyTask.id == task_id))
    if not t:
        raise HTTPException(404, "Task not found")
    if payload.status not in ("pending","done","skipped"):
        raise HTTPException(422, "Invalid status")
    t.status = payload.status  # SQLAlchemy convierte al Enum
    db.commit()
    db.refresh(t)
    return t