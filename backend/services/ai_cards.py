# backend/services/ai_cards.py
from __future__ import annotations
import os, json
from typing import List, Tuple
from openai import OpenAI
from .ai_common import extract_text_by_page, page_windows, OPENAI_MODEL_CARDS

SYSTEM = (
    "Eres tutor académico. A partir de un texto, generas tarjetas de estudio breves y útiles "
    "(pregunta y respuesta) en español, concisas, una idea por tarjeta."
    "No inventes si el texto no lo respalda. Responde SOLO JSON con lista de objetos: "
    '[{"question":"...","answer":"...","page":N}, ...]'
)

PROMPT = (
    "Genera {per_page} tarjetas por página (máximo), variadas, claras, y útiles para repasar. "
    "Evita preguntas triviales. Texto de páginas {p1}-{p2}:\n\n{chunk}\n\n"
    "Responde SOLO JSON (lista)."
)

def generate_cards_from_pdf_ai(pdf_path: str, per_page: int = 2) -> List[Tuple[str,str,int]]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pages = extract_text_by_page(pdf_path)
    res: List[Tuple[str,str,int]] = []

    for p1, p2, chunk in page_windows(pages, window_size=8):
        user = PROMPT.format(p1=p1, p2=p2, chunk=chunk[:12000], per_page=per_page)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL_CARDS,
            messages=[
                {"role":"system","content":SYSTEM},
                {"role":"user","content":user}
            ],
            temperature=0.5,
        )
        txt = resp.choices[0].message.content.strip()
        if txt.startswith("```"):
            txt = txt.strip("`")
            if txt.startswith("json"):
                txt = txt[4:].strip()
        try:
            data = json.loads(txt)
            for item in data:
                q = str(item.get("question","")).strip()
                a = str(item.get("answer","")).strip()
                pg = int(item.get("page", p1))
                if q and a and (p1 <= pg <= p2):
                    res.append((q, a, pg))
        except Exception:
            pass
    return res
