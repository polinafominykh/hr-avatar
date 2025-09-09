import React, { useEffect, useState } from "react";
import FileDrop from "../components/FileDrop";
import { postResume, getPrescreen } from "../api";
import { useStore } from "../store";
import ProgressBar from "../components/ProgressBar";
import ScanProgress from "../components/ScanProgress";

export default function Resumes() {
  const { setTab } = useStore();
  const [list,setList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);


  const load = async()=> setList(await getPrescreen());
  useEffect(()=>{ load(); },[]);

  return (
    <div className="space-y-6">
          <FileDrop
      accept=".pdf,.docx,.rtf"
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
        <table className="w-full text-sm overflow-hidden rounded-[var(--radius)] border border-[var(--card-border)]">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2 text-left">Кандидат</th>
              <th className="p-2">Оценка</th>
              <th className="p-2">Действие</th>
            </tr>
          </thead>
          <tbody>
            {list.map((r:any)=>(
              <tr key={r.id} className="border-t">
                <td className="p-2">{r.name}</td>
                <td className="p-2">
                  <div className="flex items-center gap-3">
                    <div className="w-12 text-right">{Math.round((r.prescore || 0) * 100)}%</div>
                    <div className="flex-1">
                      <ProgressBar value={Math.round((r.prescore || 0) * 100)} />
                    </div>
                  </div>
                </td>
                <td className="p-2 text-center">
                  <button
                  className="w-full px-4 py-2 bg-[#0044BB] hover:bg-[#003399] text-white font-medium rounded-lg shadow-md transition"
                  onClick={()=>{ useStore.setState({ currentCandidateId:r.id }); setTab("int"); }}>
                  Интервью
                </button>

                </td>
              </tr>
            ))}
            {list.length===0 && <tr><td className="p-3" colSpan={3}>Пока пусто — загрузите резюме</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
