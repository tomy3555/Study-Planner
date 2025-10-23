# backend/services/pdf_persist.py
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import delete
from ..models import Topic, Card

def save_topics(db: Session, summary_id: int, topics: list[tuple[str,int,int]]):
    db.execute(delete(Topic).where(Topic.summary_id == summary_id))
    for title, sp, ep in topics:
        db.add(Topic(summary_id=summary_id, title=title, start_page=sp, end_page=ep))
    db.commit()

def save_cards(db: Session, summary_id: int, cards: list[tuple[str,str,int]]):
    # no borramos todas por defecto; si querés “recrear”, antes hacé un delete
    for q, a, pg in cards:
        db.add(Card(summary_id=summary_id, origin_page=pg, question=q, answer=a))
    db.commit()
