# StudyPlanner SRS

Planificador de estudio con **repetición espaciada (SRS)**.  
Dados un **resumen** (páginas) y una **fecha de examen**, genera un **plan diario** que reparte lectura, práctica (parciales/ejercicios) y revisiones de tarjetas.  
Stack: **HTML/CSS/JS** (frontend) + **FastAPI (Python)** + **MySQL**.

> V1: crear tarjetas (pregunta/respuesta), repasar, ver próximos pendientes y **generar plan** por resumen.  
> V2: métricas por día, dificultad y ajuste del algoritmo, multiusuario, gráficos.

---

## ✨ Funcionalidades (V1)

- **Materias** y **Resúmenes** (con páginas totales y fecha de examen).
- **Generación de plan** por resumen:
  - Días de **lectura** (distribuye páginas).
  - Días de **práctica** (parciales/ejercicios).
  - **SRS diario** (revisiones de tarjetas).
  - Días **buffer** antes del examen.
- Vista **“Hoy”**: tareas diarias (marcar como hechas).
- Banco de **tarjetas** (Q/A) y **revisiones** con SRS simple.

---

## 🧱 Modelo de datos (resumen)

Tablas principales:

- `subjects` — materias  
- `summaries` — resúmenes (páginas, fecha de examen)  
- `study_plans` — plan generado por resumen  
- `study_tasks` — tareas diarias (lectura/práctica/revisión)  
- `old_exams` — parciales/ejercicios sugeridos para práctica  
- `cards` — tarjetas SRS (pregunta/respuesta)  
- `reviews` — historial de revisiones SRS

> El script SQL completo está en `docs/schema.sql` (o copialo de este README).

---

## 🧰 Requisitos

- **Python 3.11+**
- **MySQL 8+** (podés gestionarlo con **MySQL Workbench**)
- Navegador moderno

---
