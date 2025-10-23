export const API = "http://127.0.0.1:8000";
export const $ = (s, root=document) => root.querySelector(s);
export const j = (r) => r.ok ? r.json() : r.json().then(e => { throw new Error(e.detail || r.statusText); });
export const setStatus = (msg, type="info") => {
  let s = document.getElementById("status"); if (!s) return;
  s.textContent = msg || "";
  s.style.color = type === "error" ? "#ef4444" : type === "ok" ? "#22c55e" : "#9aa4b2";
};
