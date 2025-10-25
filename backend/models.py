from __future__ import annotations
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import (
    String, Integer, Date, DateTime, ForeignKey,
    UniqueConstraint, Numeric, func, Text  # 👈 Text de SQLAlchemy
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base


# ======================
# Enums de negocio
# ======================
class TaskType(PyEnum):
    READ = "read"
    PRACTICE = "practice"
    REVIEW = "review"
    REST = "rest"


class TaskStatus(PyEnum):
    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"


# ======================
# subjects
# ======================
class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones
    summaries: Mapped[list["Summary"]] = relationship(
        "Summary", back_populates="subject", cascade="all, delete-orphan"
    )


# ======================
# summaries
# ======================
class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones
    subject: Mapped[Subject] = relationship("Subject", back_populates="summaries")
    plan: Mapped["StudyPlan"] = relationship(
        "StudyPlan", back_populates="summary", uselist=False, cascade="all, delete-orphan"
    )


# ======================
# study_plans
# ======================
class StudyPlan(Base):
    __tablename__ = "study_plans"
    __table_args__ = (
        UniqueConstraint("summary_id", name="uq_plan_by_summary"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summary_id: Mapped[int] = mapped_column(
        ForeignKey("summaries.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # DECIMAL(4,3) en MySQL
    read_ratio: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    buffer_days: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones
    summary: Mapped[Summary] = relationship("Summary", back_populates="plan")
    tasks: Mapped[list["StudyTask"]] = relationship(
        "StudyTask", back_populates="plan", cascade="all, delete-orphan"
    )


# ======================
# study_tasks
# ======================
class StudyTask(Base):
    __tablename__ = "study_tasks"
    __table_args__ = (
        UniqueConstraint("plan_id", "day_date", "task_type", name="uq_task_per_day_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_date: Mapped[date] = mapped_column(Date, nullable=False)

    task_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "read"/"review"/"practice"/"rest"

    # Campos específicos según tipo
    start_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    practice_items: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default="pending"  
    )

    # Relaciones
    plan: Mapped[StudyPlan] = relationship("StudyPlan", back_populates="tasks")


# ======================
# topics
# ======================
class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("summary_id", "start_page", name="uq_topic_range"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summary_id: Mapped[int] = mapped_column(
        ForeignKey("summaries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)


# ======================
# cards
# ======================
class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summary_id: Mapped[int] = mapped_column(
        ForeignKey("summaries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    origin_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)  
    answer: Mapped[str] = mapped_column(Text, nullable=False)    

# ======================
# Users
# ======================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    # email_norm es columna generada en MySQL; en ORM la definimos solo para lectura
    email_norm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_verified: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.current_timestamp())