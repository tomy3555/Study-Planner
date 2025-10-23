# backend/services/ai_common.py
from __future__ import annotations
import os
from typing import Iterable, List
import pdfplumber

OPENAI_MODEL_TOPICS = os.getenv("OPENAI_MODEL_TOPICS", "gpt-4o-mini")
OPENAI_MODEL_CARDS  = os.getenv("OPENAI_MODEL_CARDS",  "gpt-4o-mini")

def extract_text_by_page(pdf_path: str) -> List[str]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            try:
                txt = p.extract_text() or ""
            except Exception:
                txt = ""
            pages.append(txt)
    return pages

def page_windows(pages: List[str], window_size: int = 10) -> Iterable[tuple[int, int, str]]:
    """
    Devuelve bloques de texto con (start_page_1based, end_page_1based, text)
    """
    n = len(pages)
    i = 0
    while i < n:
        j = min(n, i + window_size)
        block = "\n\n".join(
            f"[Página {k+1}]\n{pages[k]}" for k in range(i, j)
        )
        yield (i+1, j, block)
        i = j
