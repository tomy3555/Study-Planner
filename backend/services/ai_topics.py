# backend/services/ai_topics.py
from __future__ import annotations
import os, json
from typing import List, Tuple
from openai import OpenAI
from .ai_common import extract_text_by_page, page_windows, OPENAI_MODEL_TOPICS

SYSTEM = (
    "Eres un asistente que ayuda a estructurar apuntes académicos. "
    "Tu tarea: detectar secciones (temas) con un TÍTULO breve y rango de páginas. "
    "Responde SIEMPRE en JSON puro (sin comentarios), como lista de objetos: "
    '[{"title":"...","startPage":N,"endPage":M}, ...]. '
    "Los rangos no pueden solaparse y deben cubrir sólo donde haya un encabezado claro."
)

PROMPT = (
    "Tengo un resumen académico. Te paso texto por páginas. "
    "Devuélveme títulos de secciones con rango [startPage..endPage]. "
    "Si no ves un título claro, no inventes. Conciso, útil para un índice. "
    "Bloque de páginas {p1}-{p2}:\n\n{chunk}\n\n"
    "Responde SOLO JSON (lista)."
)

def extract_topics_from_pdf_ai(pdf_path: str) -> List[Tuple[str,int,int]]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pages = extract_text_by_page(pdf_path)
    agg: List[Tuple[str,int,int]] = []

    for p1, p2, chunk in page_windows(pages, window_size=10):
        user = PROMPT.format(p1=p1, p2=p2, chunk=chunk[:12000])  # límite defensivo
        resp = client.chat.completions.create(
            model=OPENAI_MODEL_TOPICS,
            messages=[
                {"role":"system","content":SYSTEM},
                {"role":"user","content":user}
            ],
            temperature=0.2,
        )
        txt = resp.choices[0].message.content.strip()
        # puede venir envuelto en ```json ...```
        if txt.startswith("```"):
            txt = txt.strip("`")
            if txt.startswith("json"):
                txt = txt[4:].strip()
        try:
            data = json.loads(txt)
            for item in data:
                title = str(item.get("title","")).strip()
                sp = int(item.get("startPage",0))
                ep = int(item.get("endPage",0))
                if title and sp>=p1 and ep<=p2 and sp<=ep:
                    agg.append((title, sp, ep))
        except Exception:
            # ignora bloque defectuoso, seguimos con el resto
            pass

    # Merge sencillo: si dos temas consecutivos tienen el mismo título, unir
    merged: List[Tuple[str,int,int]] = []
    for t in agg:
        if merged and merged[-1][0] == t[0] and t[1] == merged[-1][2] + 1:
            merged[-1] = (merged[-1][0], merged[-1][1], t[2])
        else:
            merged.append(t)
    return merged
