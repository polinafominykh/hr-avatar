import React from "react";

type Props = { tab: string; setTab: (t: string) => void };

export default function TabBar({ tab, setTab }: Props) {
  const tabs = [
    { id: "vac", label: "Вакансия" },
    { id: "res", label: "Резюме" },
    { id: "int", label: "Интервью" },
    { id: "rep", label: "Отчёт" },
  ];

  return (
    <div className="w-full grid grid-cols-4 gap-3">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => setTab(t.id)}
          className={[
            "w-full rounded-xl px-5 py-3 text-sm transition border active:scale-95",
            "text-center",
            tab === t.id
              ? "bg-[var(--vtb-blue)] border-[var(--vtb-blue)] text-white shadow"
              : "bg-white border-[var(--card-border)] text-gray-700 hover:bg-[var(--vtb-blue-soft)] hover:border-[var(--vtb-blue)]",
          ].join(" ")}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}