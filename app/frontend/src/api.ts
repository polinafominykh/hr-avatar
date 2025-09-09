import axios from "axios";
const API = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000" });

export async function postVacancy(file: File) {
  const fd = new FormData(); fd.append("file", file);
  return (await API.post("/vacancy", fd)).data;
}
export async function postResume(file: File) {
  const fd = new FormData(); fd.append("file", file);
  return (await API.post("/resume", fd)).data;
}
export async function getPrescreen() { return (await API.get("/prescreen")).data; }
export function wsAudio(candidateId: string) {
  const base = import.meta.env.VITE_WS_URL || "ws://127.0.0.1:8000";
  return new WebSocket(`${base}/audio?candidate_id=${candidateId}`);
}
export async function getReport(candidateId: string) {
  const res = await API.get(`/report/${candidateId}`, { responseType: "blob" });
  return res.data as Blob;
}
