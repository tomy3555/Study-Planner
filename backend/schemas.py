from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, conint, condecimal


# ============================
# camelCase en el JSON
# ============================
def to_camel(s: str) -> str:
    parts = s.split('_')
    return parts[0] + ''.join(p.title() for p in parts[1:])

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


# ============================
# Subjects
# ============================
class SubjectCreate(CamelModel):
    name: str

class SubjectOut(CamelModel):
    id: int
    name: str
    created_at: datetime


# ============================
# Summaries
# ============================
class SummaryCreate(CamelModel):
    subject_id: int
    title: str
    pages: conint(gt=0)  # entero > 0
    exam_date: date

class SummaryOut(CamelModel):
    id: int
    subject_id: int
    title: str
    pages: int
    exam_date: date
    created_at: datetime


# ============================
# Study Plans
# ============================
class PlanGenerateIn(CamelModel):
    summary_id: int
    start_date: date          # normalmente hoy
    end_date: date            # normalmente exam_date
    read_ratio: condecimal(gt=0, lt=1, max_digits=4, decimal_places=3)  # ej. 0.6
    buffer_days: conint(ge=0, le=3) = 1     # “colchón” de 0..3 días
    review_quota: conint(ge=0, le=200) = 20 # tarjetas por día sugeridas

class StudyPlanOut(CamelModel):
    id: int
    summary_id: int
    start_date: date
    end_date: date
    read_ratio: float
    buffer_days: int
    created_at: datetime


# ============================
# Study Tasks
# ============================
class StudyTaskOut(CamelModel):
    id: int
    plan_id: int
    day_date: date
    task_type: str
    start_page: int | None = None
    end_page: int | None = None
    practice_items: int | None = None
    review_quota: int | None = None
    notes: str | None = None
    status: str

class TaskPatchIn(CamelModel):
    status: str  # "pending" | "done" | "skipped"   