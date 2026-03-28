"use client";

import { useState } from "react";
import { useNewChat } from "@/hooks/use-new-chat";
import ChatHistoryList from "./chat-history-list";
import SampleQuestions from "./sample-questions";

export default function Sidebar() {
  const { mutate: createChat, isPending } = useNewChat();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex h-full flex-col border-r border-zinc-200 bg-zinc-50 transition-all ${
        collapsed ? "w-12" : "w-72"
      }`}
    >
      <div className="flex items-center justify-between p-2">
        {!collapsed && (
          <div className="px-2">
            <h2 className="text-lg font-bold text-zinc-800">
              Instacart BI Agent
            </h2>
            <p className="text-xs text-zinc-500">
              Ask questions about grocery data
            </p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="shrink-0 rounded p-1.5 text-zinc-500 hover:bg-zinc-200"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {collapsed ? (
              <>
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="px-3 pb-3">
            <button
              onClick={() => createChat()}
              disabled={isPending}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              + New Chat
            </button>
          </div>

          <div className="border-t border-zinc-200 px-3 py-2">
            <p className="mb-1 text-xs font-semibold text-zinc-500 uppercase">
              Chat History
            </p>
            <div className="max-h-60 overflow-y-auto">
              <ChatHistoryList />
            </div>
          </div>

          <div className="mt-auto border-t border-zinc-200 px-3 py-2">
            <p className="mb-1 text-xs font-semibold text-zinc-500 uppercase">
              Sample Questions
            </p>
            <SampleQuestions />
          </div>
        </>
      )}
    </aside>
  );
}
