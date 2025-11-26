# StudyPlanner SRS

Planificador de estudio con **repetición espaciada (SRS)**.  
Dado un **resumen** (n° de páginas) y una **fecha de examen**, genera un **plan diario** que reparte lectura, práctica y revisión mediante tarjetas.

**Stack:** Front **HTML/CSS/JS** · Back **FastAPI (Python)** · **MySQL**  
**Auth:** JWT (hash **Argon2**) · Cookies HttpOnly / localStorage

> **V1 (actual)**: materias, resúmenes, plan por resumen, tareas, tarjetas, IA opcional para tópicos y tarjetas.  
> **V2 (roadmap)**: métricas, dificultad adaptable, UI pulida, multiusuario completo, gráficos.

---

##  Funcionalidades (V1)

- **Materias** (`subjects`) y **Resúmenes** (`summaries`)
- **Generación de plan** (`study_plans` + `study_tasks`)
- **Tareas** filtrables por fecha
- **Tarjetas** Q/A (`cards`)
- **Subida de PDF** por resumen
- **IA opcional**:
  - Extraer **tópicos**
  - Generar **tarjetas** a partir del PDF

---

##  Modelo de datos

Tablas principales:

- `users` — usuarios (email normalizado, password Argon2)
- `subjects` — materias
- `summaries` — resúmenes con PDF
- `study_plans` — plan generado
- `study_tasks` — tareas (READ/PRACTICE/REVIEW/REST)
- `topics` — tópicos por rango de páginas
- `cards` — tarjetas de estudio

> El script SQL está en `docs/schema.sql`.

---

##  Requisitos

- Python **3.11+**
- MySQL **8+**
- Navegador moderno

---

