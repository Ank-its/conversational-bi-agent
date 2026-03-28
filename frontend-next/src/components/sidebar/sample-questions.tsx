"use client";

import { SAMPLE_QUESTIONS } from "@/lib/constants";
import { useChat } from "@/providers/chat-provider";

export default function SampleQuestions() {
  const { send, isSending, activeSessionId } = useChat();

  return (
    <div className="flex flex-col gap-1">
      {SAMPLE_QUESTIONS.map((q) => (
        <button
          key={q}
          disabled={isSending || !activeSessionId}
          onClick={() => send(q)}
          className="w-full rounded border border-zinc-200 px-3 py-1.5 text-left text-xs text-zinc-600 transition-colors hover:bg-zinc-100 disabled:opacity-50"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
