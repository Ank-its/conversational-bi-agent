"use client";

import { useState, type FormEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
  isPending: boolean;
}

export default function ChatInput({ onSend, onStop, isPending }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isPending) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-2 border-t border-zinc-200 bg-white p-4"
    >
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask a question about Instacart data..."
        disabled={isPending}
        className="flex-1 rounded-lg border border-zinc-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-blue-500 disabled:bg-zinc-50 disabled:text-zinc-400"
      />
      {isPending ? (
        <button
          type="button"
          onClick={onStop}
          className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-700"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="4" y="4" width="16" height="16" rx="2" />
          </svg>
          Stop
        </button>
      ) : (
        <button
          type="submit"
          disabled={!value.trim()}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
        >
          Send
        </button>
      )}
    </form>
  );
}
