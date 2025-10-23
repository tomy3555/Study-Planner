from datetime import date
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi import UploadFile, File
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

from .services.ai_topics import extract_topics_from_pdf_ai
from .services.ai_cards import generate_cards_from_pdf_ai   
from .services.pdf_persist import save_topics as save_topics_db, save_cards as save_cards_db

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from sqlalchemy import text

from pathlib import Path
from dotenv import load_dotenv

    

from .db import get_db
from .models import Subject, Summary
from .models import StudyPlan, StudyTask
from .models import Topic, Card
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

load_dotenv(Path(__file__).with_name(".env"))
import os
k = os.getenv("OPENAI_API_KEY", "")
print("[OpenAI] KEY cargada:", "(vacía)" if not k else f"{k[:7]}...{k[-4:]} (len={len(k)})")

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

@app.post("/api/summaries/{summary_id}/upload-pdf")
def upload_summary_pdf(summary_id: int, file: UploadFile = File(...)):
    filename = f"summary_{summary_id}.pdf"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {"ok": True, "path": path}

@app.post("/api/summaries/{summary_id}/ai/extract-topics")
def ai_extract_topics(summary_id: int, db: Session = Depends(get_db)):
    # validar summary
    s = db.scalar(select(Summary).where(Summary.id == summary_id))
    if not s:
        raise HTTPException(404, "Summary not found")

    pdf_path = os.path.join(UPLOAD_DIR, f"summary_{summary_id}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF no subido para este summary.")

    topics = extract_topics_from_pdf_ai(pdf_path)
    if not topics:
        return {"ok": True, "topics": 0, "note": "La IA no detectó títulos claros."}
    save_topics_db(db, summary_id, topics)
    return {"ok": True, "topics": len(topics)}

@app.post("/api/summaries/{summary_id}/ai/generate-cards")
def ai_generate_cards(summary_id: int, db: Session = Depends(get_db), per_page: int = 2):
    s = db.scalar(select(Summary).where(Summary.id == summary_id))
    if not s:
        raise HTTPException(404, "Summary not found")

    pdf_path = os.path.join(UPLOAD_DIR, f"summary_{summary_id}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF no subido para este summary.")

    cards = generate_cards_from_pdf_ai(pdf_path, per_page=per_page)
    if not cards:
        return {"ok": True, "cards": 0, "note": "La IA no generó tarjetas con este texto."}
    save_cards_db(db, summary_id, cards)
    return {"ok": True, "cards": len(cards)}

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

@app.get("/api/summaries/{summary_id}/topics")
def list_topics(summary_id: int, db: Session = Depends(get_db)):
    # valida que exista el summary
    s = db.scalar(select(Summary).where(Summary.id == summary_id))
    if not s:
        raise HTTPException(404, "Summary not found")
    rows = db.execute(
        select(Topic).where(Topic.summary_id == summary_id).order_by(Topic.start_page)
    ).scalars().all()
    # devolvemos estructuras simples
    return [
        {
            "id": t.id,
            "summaryId": t.summary_id,
            "title": t.title,
            "startPage": t.start_page,
            "endPage": t.end_page,
        }
        for t in rows
    ]


@app.get("/api/summaries/{summary_id}/cards")
def list_cards(summary_id: int, db: Session = Depends(get_db)):
    s = db.scalar(select(Summary).where(Summary.id == summary_id))
    if not s:
        raise HTTPException(404, "Summary not found")
    rows = db.execute(
        select(Card).where(Card.summary_id == summary_id).order_by(Card.origin_page)
    ).scalars().all()
    return [
        {
            "id": c.id,
            "summaryId": c.summary_id,
            "topicId": c.topic_id,
            "originPage": c.origin_page,
            "question": c.question,
            "answer": c.answer,
        }
        for c in rows
    ]