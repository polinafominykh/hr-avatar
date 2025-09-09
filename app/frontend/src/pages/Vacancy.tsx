import React, { useState } from "react";
import FileDrop from "../components/FileDrop";
import { postVacancy } from "../api";
import { useStore } from "../store";

export default function Vacancy() {
  const [status,setStatus] = useState("");
  const { setTab } = useStore();

      return (
      <div className="w-full space-y-4">
        <FileDrop
        accept={".yaml,.yml"}
        onFile={(f) => {
        setStatus(`Загружен файл: ${f.name}`);
        }}
        />
        <div className="text-sm text-gray-600">{status}</div>
      </div>
    );
}
