import React, { useState } from "react";
import { getReport } from "../api";
import { useStore } from "../store";

export default function Report() {
  const { currentCandidateId, report, setReport } = useStore();
  const [busy, setBusy] = useState(false);

  const generate = async () => {
    if (!currentCandidateId) {
      alert("Нет кандидата");
      return;
    }
    setBusy(true);
    const blob = await getReport(currentCandidateId);
    const url = URL.createObjectURL(blob);
    setReport({ score: 81, pdfUrl: url, recommendation: "next" });
    setBusy(false);
  };

  return (
    <div className="space-y-4">
      <button
        disabled={busy}
        onClick={generate}
        className={`px-4 py-2 font-medium rounded-lg shadow-md transition
          ${busy
            ? "bg-gray-400 text-white cursor-not-allowed"
            : "bg-[#0044BB] hover:bg-[#003399] text-white"
          }`}
      >
        {busy ? "Генерация…" : "Сформировать отчёт"}
      </button>

      {report && (
        <div className="p-4 border rounded bg-white shadow">
          <div className="text-xl font-semibold">Итог: {report.score}%</div>
          <div className="text-sm text-gray-600 mb-2">
            Рекомендация: {report.recommendation}
          </div>
          <a
            className="inline-block mt-2 px-4 py-2 bg-[#0044BB] hover:bg-[#003399] text-white font-medium rounded-lg shadow-md transition"
            href={report.pdfUrl}
            download={`report_${currentCandidateId}.pdf`}
          >
            Скачать PDF
          </a>
        </div>
      )}
    </div>
  );
}