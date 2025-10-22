from __future__ import annotations
from datetime import date, timedelta
from math import ceil
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from ..models import StudyPlan, StudyTask, Summary, TaskType, TaskStatus
from decimal import Decimal  

def _days_inclusive(d1: date, d2: date):
    n = (d2 - d1).days
    for i in range(n + 1):
        yield d1 + timedelta(days=i)

def generate_plan(
    db: Session,
    *,
    summary_id: int,
    start_date: date,
    end_date: date,
    read_ratio: float,
    buffer_days: int,
    review_quota: int,
) -> StudyPlan:
    # 1) validar
    summary = db.scalar(select(Summary).where(Summary.id == summary_id))
    if not summary:
        raise ValueError("Summary not found")
    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")
    if not (0 < read_ratio < 1):
        raise ValueError("read_ratio must be between 0 and 1")
    if buffer_days < 0:
        buffer_days = 0

    # 2) borrar plan previo (si existe)
    existing = db.scalar(select(StudyPlan).where(StudyPlan.summary_id == summary_id))
    if existing:
        db.execute(delete(StudyTask).where(StudyTask.plan_id == existing.id))
        db.execute(delete(StudyPlan).where(StudyPlan.id == existing.id))
        db.flush()
    # 3) crear plan
    plan = StudyPlan(
        summary_id=summary_id,
        start_date=start_date,
        end_date=end_date,
       read_ratio=Decimal(str(read_ratio)),
        buffer_days=buffer_days,
    )
    db.add(plan)
    db.flush()  # ya tenemos plan.id

    # 4) calcular días
    all_days = list(_days_inclusive(start_date, end_date))
    days_total = len(all_days)
    days_effective = max(1, days_total - buffer_days)

    reading_days = max(1, round(days_effective * float(read_ratio)))
    practice_days = max(0, days_effective - reading_days)

    # 5) repartir páginas
    total_pages = summary.pages
    pages_per_day = ceil(total_pages / reading_days)

    reading_idxs  = range(0, reading_days)
    practice_idxs = range(reading_days, reading_days + practice_days)
    buffer_idxs   = range(reading_days + practice_days, days_total)

    # 6) READ
    cur = 1
    for i in reading_idxs:
        d = all_days[i]
        start_p = cur
        end_p = min(total_pages, cur + pages_per_day - 1)
        cur = end_p + 1
        db.add(StudyTask(
            plan_id=plan.id,
            day_date=d,
            task_type="read",
            start_page=start_p,
            end_page=end_p,
            notes="Lectura",
            status="pending"
        ))

    # 7) PRACTICE
    for i in practice_idxs:
        d = all_days[i]
        db.add(StudyTask(
            plan_id=plan.id,
            day_date=d,
            task_type="practice",
            practice_items=1,
            notes="Práctica (parcial/ejercicios)",
            status="pending"
        ))

    # 8) REVIEW (todos los días efectivos)
    for i in range(0, days_effective):
        d = all_days[i]
        db.add(StudyTask(
            plan_id=plan.id,
            day_date=d,
            task_type="review",
            review_quota=review_quota,
            notes="Revisión SRS",
            status="pending"
        ))

    # 9) REST (buffer)
    for i in buffer_idxs:
        d = all_days[i]
        db.add(StudyTask(
            plan_id=plan.id,
            day_date=d,
            task_type="rest",
            notes="Buffer/descanso",
            status="pending"
        ))

    db.commit()
    db.refresh(plan)
    return plan