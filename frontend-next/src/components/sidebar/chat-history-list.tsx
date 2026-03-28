"use client";

import { useChat } from "@/providers/chat-provider";

export default function ChatHistoryList() {
  const { sessions, activeSessionId, setActive } = useChat();
  const ids = Object.keys(sessions).reverse();

  if (ids.length === 0) {
    return <p className="px-3 text-sm text-zinc-400">No chats yet</p>;
  }

  return (
    <div className="flex flex-col gap-0.5">
      {ids.map((id) => {
        const isActive = id === activeSessionId;
        return (
          <button
            key={id}
            onClick={() => setActive(id)}
            className={`w-full truncate rounded px-3 py-1.5 text-left text-sm transition-colors ${
              isActive
                ? "bg-blue-100 font-semibold text-blue-900"
                : "text-zinc-600 hover:bg-zinc-100"
            }`}
          >
            {isActive ? "▸ " : ""}
            {sessions[id].title}
          </button>
        );
      })}
    </div>
  );
}
