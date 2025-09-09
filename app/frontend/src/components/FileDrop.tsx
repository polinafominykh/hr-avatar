import React, { useRef } from "react";

type Props = {
  accept?: string;
  onFile: (f: File) => void;
};

export default function FileDrop({ accept, onFile }: Props) {
  const ref = useRef<HTMLInputElement>(null);

  return (
    <div
      onClick={() => ref.current?.click()}
      className="w-full min-h-[220px] cursor-pointer rounded-[12px]
             border-2 border-dashed border-gray-300
             bg-blue-50/40 hover:bg-blue-50 p-10 text-center transition"
    >
      <p className="text-gray-700">
        Перетащите файл сюда или{" "}
        <span className="text-[#0044BB] underline">выберите</span>
      </p>
      <input
        ref={ref}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
    </div>
  );
}