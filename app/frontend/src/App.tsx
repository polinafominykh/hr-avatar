// src/App.tsx
import React from "react";
import { useStore } from "./store";
import TabBar from "./components/TabBar";
import Vacancy from "./pages/Vacancy";
import Resumes from "./pages/Resumes";
import Interview from "./pages/Interview";
import Report from "./pages/Report";

import vtbLogo from "./assets/vtb.png";
import robotAvatar from "./assets/robot.png";

export default function App() {
  const { tab, setTab } = useStore();

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-r from-[#e6f0ff] via-[#f8faff] to-[#dbeafe]">

      {/* Основная часть */}
      <main className="flex-grow w-[100vw] max-w-[1450px] mx-auto px-8 py-10">

        {/* Заголовок */}
        <header className="mb-6 flex items-center justify-center gap-4">
          <h1 className="text-4xl font-semibold tracking-tight text-[#0044BB]">
            HR-Аватар
          </h1>
          <img
            src={robotAvatar}
            alt="Robot Avatar"
            className="h-12 w-12 rounded-full border border-gray-300 shadow"
          />
        </header>

        <p className="mt-1 text-sm text-center text-gray-500">
          Цифровой ассистент подбора: Вакансия → Резюме → Интервью → Отчёт
        </p>

        {/* Вкладки */}
        <TabBar tab={tab} setTab={setTab} />

        {/* Карточка контента */}
        <div className="mt-4 w-full rounded-xl bg-white border border-gray-200 p-8 shadow">
          {tab === "vac" && <Vacancy />}
          {tab === "res" && <Resumes />}
          {tab === "int" && <Interview />}
          {tab === "rep" && <Report />}
        </div>
      </main>

      {/* Футер с логотипом ВТБ */}
      <footer className="py-6 bg-white border-t border-gray-200">
        <div className="w-[95vw] max-w-[1400px] mx-auto flex items-center justify-center gap-3">
          <img src={vtbLogo} alt="VTB" className="h-8" />
          <span className="text-sm text-gray-500"></span>
        </div>
      </footer>
    </div>
  );
}