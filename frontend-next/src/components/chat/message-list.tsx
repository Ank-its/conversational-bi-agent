"use client";

import { useEffect, useRef } from "react";
import type { StoredMessage } from "@/lib/types";
import UserBubble from "./user-bubble";
import AssistantBubble from "./assistant-bubble";

interface MessageListProps {
  messages: StoredMessage[];
  isPending: boolean;
}

export default function MessageList({ messages, isPending }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isPending]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-zinc-400">
        Start a conversation by typing a question below
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
      {messages.map((msg, i) =>
        msg.role === "user" ? (
          <UserBubble key={i} content={msg.content} />
        ) : (
          <AssistantBubble key={i} message={msg} />
        ),
      )}
      {isPending && (
        <div className="flex items-start gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-lg" title="BI Agent">
            🤖
          </div>
          <div className="rounded-2xl rounded-bl-sm border border-zinc-200 bg-white px-4 py-3 text-sm shadow-sm">
            <div className="flex items-center gap-1.5 text-zinc-400">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Thinking...
            </div>
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
