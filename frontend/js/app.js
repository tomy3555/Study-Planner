const API = "http://127.0.0.1:8000";
const $ = (sel) => document.querySelector(sel);

// helpers
const setStatus = (msg, type="info") => {
  const s = $("#status");
  s.textContent = msg || "";
  s.style.color = type === "error" ? "#ef4444" : type === "ok" ? "#22c55e" : "#9aa4b2";
};
const j = (r) => r.ok ? r.json() : r.json().then(e => { throw new Error(e.detail || r.statusText) });

// DOM refs
const subjectForm = $("#subjectForm");
const subjectName = $("#subjectName");
const subjectsList = $("#subjectsList");
const btnLoadSubjects = $("#btnLoadSubjects");

const summaryForm = $("#summaryForm");
const summarySubjectId = $("#summarySubjectId");
const summaryTitle = $("#summaryTitle");
const summaryPages = $("#summaryPages");
const summaryExamDate = $("#summaryExamDate");
const summariesList = $("#summariesList");
const btnLoadSummaries = $("#btnLoadSummaries");

const planForm = $("#planForm");
const planSummaryId = $("#planSummaryId");
const planStartDate = $("#planStartDate");
const planEndDate = $("#planEndDate");
const planReadRatio = $("#planReadRatio");
const planBufferDays = $("#planBufferDays");
const planReviewQuota = $("#planReviewQuota");

const tasksPlanId = $("#tasksPlanId");
const tasksFrom = $("#tasksFrom");
const tasksTo = $("#tasksTo");
const btnLoadTasks = $("#btnLoadTasks");
const tasksList = $("#tasksList");

// populate today defaults
const todayStr = () => new Date().toISOString().slice(0,10);
planStartDate.value = todayStr();

// API calls
async function listSubjects() {
  const r = await fetch(`${API}/api/subjects`);
  const data = await j(r);

  subjectsList.innerHTML = "";
  summarySubjectId.innerHTML = "";   // este sí (para crear Summary)

  data.forEach(s => {
    const li = document.createElement("li");
    li.textContent = `${s.id} · ${s.name}`;
    subjectsList.appendChild(li);

    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = `${s.name} (#${s.id})`;
    summarySubjectId.appendChild(opt);   // elegir subject al crear summary
  });

  setStatus(`Subjects: ${data.length}`, "ok");
}

async function createSubject(e) {
  e.preventDefault();
  const name = subjectName.value.trim();
  if (!name) return;
  const r = await fetch(`${API}/api/subjects`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  const data = await j(r);
  subjectName.value = "";
  await listSubjects();
  setStatus(`Subject creado (#${data.id})`, "ok");
}

let summariesCache = []; // para consultar examDate al cambiar selección

async function listSummaries() {
  const r = await fetch(`${API}/api/summaries`);
  const data = await j(r);
  summariesCache = data;

  summariesList.innerHTML = "";
  planSummaryId.innerHTML = "";      // acá sí llenamos el select de plan

  data.forEach(s => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>#${s.id}</strong> · ${s.title} (subject ${s.subjectId}) · páginas ${s.pages} · examen ${s.examDate}`;
    summariesList.appendChild(li);

    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = `${s.title} (#${s.id})`;
    planSummaryId.appendChild(opt);
  });

  // si hay al menos un summary, setear endDate = examDate del seleccionado
  if (data.length > 0) {
    const sel = Number(planSummaryId.value);
    const found = data.find(x => x.id === sel);
    if (found) {
      planEndDate.value = found.examDate; // ayuda para generar plan
    }
  }

  setStatus(`Summaries: ${data.length}`, "ok");
}

async function createSummary(e) {
  e.preventDefault();
  const payload = {
    subjectId: Number(summarySubjectId.value),
    title: summaryTitle.value.trim(),
    pages: Number(summaryPages.value),
    examDate: summaryExamDate.value
  };
  const r = await fetch(`${API}/api/summaries`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await j(r);
  summaryTitle.value = "";
  summaryPages.value = "";
  summaryExamDate.value = "";
  await listSummaries();
  setStatus(`Summary creado (#${data.id})`, "ok");
}

async function generatePlan(e) {
  e.preventDefault();
  const payload = {
    summaryId: Number(planSummaryId.value),
    startDate: planStartDate.value,
    endDate: planEndDate.value,
    readRatio: Number(planReadRatio.value),
    bufferDays: Number(planBufferDays.value),
    reviewQuota: Number(planReviewQuota.value)
  };
  const r = await fetch(`${API}/api/plans/generate`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await j(r);
  tasksPlanId.value = data.id;

  // 👇 carga automática de tareas del plan recién creado
  tasksFrom.value = ""; // opcional: limpiar rango
  tasksTo.value = "";
  await listTasks();

  setStatus(`Plan generado (#${data.id})`, "ok");
}

async function listTasks() {
  const pid = Number(tasksPlanId.value);
  if (!pid) return setStatus("Poné un Plan ID", "error");
  const params = new URLSearchParams();
  if (tasksFrom.value) params.set("from_date", tasksFrom.value);
  if (tasksTo.value) params.set("to_date", tasksTo.value);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const r = await fetch(`${API}/api/plans/${pid}/tasks${qs}`);
  const data = await j(r);
  renderTasks(data);
  setStatus(`Tareas: ${data.length}`, "ok");
}

function renderTasks(list) {
  tasksList.innerHTML = "";
  list.forEach(t => {
    const card = document.createElement("div");
    card.className = "card";
    const badge = `<span class="badge ${t.status}">${t.status}</span>`;
    let extra = "";
    if (t.taskType === "read")   extra = `pág. ${t.startPage}-${t.endPage}`;
    if (t.taskType === "review") extra = `quota: ${t.reviewQuota}`;
    if (t.taskType === "practice") extra = `items: ${t.practiceItems ?? 1}`;

    card.innerHTML = `
      <div class="row">
        <strong>${t.dayDate}</strong>
        <span class="badge">${t.taskType}</span>
        ${badge}
      </div>
      <div>${t.notes ?? ""}</div>
      <div class="muted">${extra}</div>
      <div class="actions">
        <button data-id="${t.id}" data-status="done">✔ Hecha</button>
        <button data-id="${t.id}" data-status="skipped">⏭ Omitir</button>
        <button data-id="${t.id}" data-status="pending">↺ Pendiente</button>
      </div>
    `;
    tasksList.appendChild(card);
  });

  // delegate clicks
  tasksList.addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-id]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    const status = btn.dataset.status;
    try {
      const r = await fetch(`${API}/api/tasks/${id}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status })
      });
      await j(r);
      await listTasks();
      setStatus(`Task #${id} → ${status}`, "ok");
    } catch(err) {
      setStatus(err.message, "error");
    }
  }, { once: true }); // reatach per render para evitar duplicados
}

// wire events
subjectForm.addEventListener("submit", (e) => createSubject(e).catch(err => setStatus(err.message, "error")));
btnLoadSubjects.addEventListener("click", () => listSubjects().catch(err => setStatus(err.message, "error")));
summaryForm.addEventListener("submit", (e) => createSummary(e).catch(err => setStatus(err.message, "error")));
btnLoadSummaries.addEventListener("click", () => listSummaries().catch(err => setStatus(err.message, "error")));
planForm.addEventListener("submit", (e) => generatePlan(e).then(listSummaries).catch(err => setStatus(err.message, "error")));
btnLoadTasks.addEventListener("click", () => listTasks().catch(err => setStatus(err.message, "error")));

// first load
listSubjects().then(listSummaries).catch(() => {});
