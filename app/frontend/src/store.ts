import { create } from "zustand";
type Tab = "vac"|"res"|"int"|"rep";
type Evidence = { skill:string; level:"none"|"weak"|"strong"; quote?:string };

export const useStore = create<{
  tab: Tab; setTab:(t:Tab)=>void;
  currentCandidateId?: string;
  prescreen: any[]; setPrescreen:(x:any[])=>void;
  transcript: string[]; addLine:(s:string)=>void;
  evidences: Evidence[]; addEv:(e:Evidence)=>void;
  report?: { score:number; pdfUrl?:string; recommendation?:string }; setReport:(r:any)=>void;
}>(set=>({
  tab:"vac", setTab:(t)=>set({tab:t}),
  currentCandidateId: undefined,
  prescreen: [], setPrescreen:(x)=>set({prescreen:x}),
  transcript: [], addLine:(s)=>set(s0=>({transcript:[...s0.transcript, s]})),
  evidences: [], addEv:(e)=>set(s0=>({evidences:[...s0.evidences, e]})),
  report: undefined, setReport:(r)=>set({report:r}),
}));
