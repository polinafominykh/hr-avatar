import React, { useEffect, useState } from "react";

const steps = [
  "Сканируем навыки…",
  "Проверяем опыт…",
  "Генерируем вопросы…",
  "Обновляем оценку…",
];

export default function ScanProgress({ show }: { show: boolean }) {
  const [i, setI] = useState(0);

  useEffect(() => {
    if (!show) return;
    const id = setInterval(() => setI((x) => (x + 1) % steps.length), 1200);
    return () => clearInterval(id);
  }, [show]);

  if (!show) return null;

  return (
    <div className="mt-3 rounded-lg border border-gray-200 bg-white p-3 shadow-sm flex items-center gap-3">
      <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-600" />
      <span className="text-sm text-gray-700">{steps[i]}</span>
    </div>
  );
}