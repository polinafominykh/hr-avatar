import React, { useRef, useState } from "react";
import { useStore } from "../store";
import { wsAudio } from "../api";

export default function Interview() {
  const { currentCandidateId, transcript, addLine, setTab } = useStore();
  const wsRef = useRef<WebSocket|null>(null);
  const [running,setRunning] = useState(false);

  const start = ()=>{
    if(!currentCandidateId){ alert("Выберите кандидата в Resumes"); return; }
    const ws = wsAudio(currentCandidateId);
    wsRef.current = ws;
    ws.onopen = ()=> setRunning(true);
    ws.onmessage = (e)=>{ try{ const d=JSON.parse(e.data);
      if(d.partial) addLine(d.partial); if(d.final) addLine(d.final); }catch{} };
    ws.onclose = ()=> setRunning(false);
  };
  const stop = ()=>{ wsRef.current?.close(); setRunning(false); };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        {!running ? (
  <button
    onClick={start}
    className="px-4 py-2 bg-[#0044BB] hover:bg-[#003399] text-white font-medium rounded-lg shadow-md transition"
  >
    Start
  </button>
) : (
  <button
    onClick={stop}
    className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg shadow-md transition"
  >
    Stop
  </button>
)}

<button
  onClick={() => setTab("rep")}
  className="px-4 py-2 bg-[#0044BB] hover:bg-[#003399] text-white font-medium rounded-lg shadow-md transition ml-2"
>
  Подвести итог
</button>

      </div>
      <div className="w-full h-80 overflow-auto rounded-[var(--radius)] border border-[var(--card-border)] bg-white p-4 text-sm">
        {transcript.length? transcript.join("\n") : "Субтитры появятся здесь…"}
      </div>
    </div>
  );
}
