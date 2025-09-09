import React from "react";
export default function ProgressBar({ value }:{ value:number }) {
  const v = Math.max(0, Math.min(100, value|0));
  return (
    <div className="w-full h-3 rounded-full bg-gray-200 overflow-hidden">
      <div className="h-full bg-blue-600 transition-all" style={{ width: `${v}%` }} />
    </div>
  );
}
