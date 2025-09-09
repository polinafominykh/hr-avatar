import React, { useEffect, useState } from "react";
import FileDrop from "../components/FileDrop";
import { postResume, getPrescreen } from "../api";
import ScanProgress from "../components/ScanProgress";

type Row = {
  skill: string;
  weight: number;
  have: boolean;
  in_resume: boolean;
  score: number;
  note?: string | null;
};

export default function Resumes() {
  const [rows, setRows] = useState<Row[]>([]);
  const [missing, setMissing] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    const data = await getPrescreen();
    setRows(data.table || []);
    setMissing(data.top_missing || []);
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      <FileDrop
        accept=".pdf,.doc,.docx,.rtf"
        onFile={async (f) => {
          setLoading(true);
          try {
            await postResume(f);
            await load();
          } finally {
            setLoading(false);
          }
        }}
      />

      <ScanProgress show={loading} />

      <div>
        <div className="font-medium mb-2">Прескрининг</div>

        {rows.length === 0 && !loading ? (
          <div className="p-3 text-gray-600 rounded-lg border border-[var(--card-border)] bg-white">
            Пока пусто — загрузите резюме
          </div>
        ) : (
          <table className="w-full text-sm overflow-hidden rounded-[var(--radius)] border border-[var(--card-border)] bg-white">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-2 text-left">Навык</th>
                <th className="p-2 text-center">Вес</th>
                <th className="p-2 text-center">В резюме</th>
                <th className="p-2 text-center">Баллы</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.skill} className="border-t">
                  <td className="p-2">{r.skill}</td>
                  <td className="p-2 text-center">{r.weight}</td>
                  <td className="p-2 text-center">
                    {r.in_resume || r.have ? (
                      <span className="px-2 py-0.5 rounded bg-green-50 text-green-700">Да</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-red-50 text-red-700">Нет</span>
                    )}
                  </td>
                  <td className="p-2 text-center">{r.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {missing.length > 0 && (
          <div className="mt-4">
            <div className="text-sm text-gray-500 mb-1">Стоит уточнить/добрать:</div>
            <div className="flex flex-wrap gap-2">
              {missing.map((s) => (
                <span key={s} className="px-2 py-1 rounded bg-blue-50 text-blue-700 text-xs">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
