import React, { useState } from "react";
import { getPrescreen, postReport } from "../api";
import { useStore } from "../store";

type PrescreenRow = {
  skill: string;
  weight: number;
  have: boolean;
  in_resume: boolean;
  score: number;
  note?: string | null;
};

export default function Report() {
  const {
    currentCandidateId,
    vacancy,
    resume,
    evidences,
    report,
    setReport,
  } = useStore() as any;

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const buildPayload = async () => {

    const hasVacancyWeights =
      vacancy && vacancy.weights && Object.keys(vacancy.weights).length > 0;
    const hasResumeSkills =
      resume && Array.isArray(resume.skills) && resume.skills.length > 0;

    if (hasVacancyWeights && hasResumeSkills) {
      const ev = (evidences || []).map((e: any) => ({
        skill: e.skill,
        text: e.quote || e.text || e.snippet || "",
        t: e.t ?? e.t0 ?? 0,
        source: e.source || "interview",
      }));

      return {
        vacancy: {
          title: vacancy.title || "",
          description: vacancy.description || "",
          weights: vacancy.weights || {},
        },
        resume: {
          text: resume.text || "",
          skills: resume.skills || [],
        },
        evidences: ev,
      };
    }


    const data = await getPrescreen();
    const table: PrescreenRow[] = data?.table || [];

    const weights = Object.fromEntries(
      table.map((r) => [r.skill, Number(r.weight) || 0])
    );
    const skills = table
      .filter((r) => r.in_resume || r.have)
      .map((r) => r.skill);

    return {
      vacancy: { weights },
      resume: { skills },
      evidences: [],
    };
  };

  const generate = async () => {
    if (!currentCandidateId) {
      alert("Нет кандидата");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = await buildPayload();
      const out = await postReport(payload);

      setReport({
        score: out.score ?? 0,
        pdfUrl: out.url_pdf,
        recommendation: (out.flags && out.flags.length) ? "check" : "next",
        flags: out.flags || [],
      });
    } catch (e: any) {
      setError(e?.message || "Не удалось сформировать отчёт");
    } finally {
      setBusy(false);
    }
  };

  const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
  const pdfHref =
    report?.pdfUrl && report.pdfUrl.startsWith("/")
      ? API_BASE + report.pdfUrl
      : report?.pdfUrl || "";

  return (
    <div className="space-y-4">
      <button
        disabled={busy}
        onClick={generate}
        className={`px-4 py-2 font-medium rounded-lg shadow-md transition
          ${busy ? "bg-gray-400 text-white cursor-not-allowed"
                 : "bg-[#0044BB] hover:bg-[#003399] text-white"}`}
      >
        {busy ? "Генерация…" : "Сформировать отчёт"}
      </button>

      {error && (
        <div className="p-3 rounded bg-red-50 text-red-700 text-sm">{error}</div>
      )}

      {report && (
        <div className="p-4 border rounded bg-white shadow space-y-2">
          <div className="text-xl font-semibold">
            Итог: {Math.round(report.score)}%
          </div>

          {Array.isArray((report as any).flags) && (report as any).flags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {(report as any).flags.map((f: string) => (
                <span key={f} className="px-2 py-1 rounded bg-amber-50 text-amber-800 text-xs">
                  ⚠️ {f}
                </span>
              ))}
            </div>
          )}

          <div className="text-sm text-gray-600">
            Рекомендация: {report.recommendation}
          </div>

          {pdfHref && (
            <a
              className="inline-block mt-2 px-4 py-2 bg-[#0044BB] hover:bg-[#003399] text-white font-medium rounded-lg shadow-md transition"
              href={pdfHref}
              download={`report_${currentCandidateId}.pdf`}
              target="_blank"
              rel="noreferrer"
            >
              Скачать PDF
            </a>
          )}
        </div>
      )}
    </div>
  );
}