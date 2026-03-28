"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { StoredMessage } from "@/lib/types";
import UserBubble from "./user-bubble";
import AssistantBubble from "./assistant-bubble";

interface MessageListProps {
  messages: StoredMessage[];
  isPending: boolean;
  streamingPlan?: string;
  streamingAgent?: string;
  streamingPhase?: "idle" | "planning" | "executing" | "answering";
}

function BlinkingCursor() {
  return <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-emerald-500" />;
}

function StreamingBubble({ phase, planText, agentText }: {
  phase: "planning" | "executing" | "answering";
  planText: string;
  agentText: string;
}) {
  const [planOpen, setPlanOpen] = useState(true);

  return (
    <div className="flex items-start gap-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-lg" title="BI Agent">
        🤖
      </div>
      <div className="max-w-[80%] space-y-2">
        {/* Plan section — collapsible */}
        {(phase === "planning" || planText) && (
          <details open={planOpen} onToggle={(e) => setPlanOpen((e.target as HTMLDetailsElement).open)}
            className="rounded-2xl rounded-bl-sm border border-zinc-200 bg-white text-sm shadow-sm overflow-hidden">
            <summary className="cursor-pointer px-4 py-2.5 font-medium text-emerald-600 select-none flex items-center gap-1.5">
              <svg className={`h-3.5 w-3.5 transition-transform ${planOpen ? "rotate-90" : ""}`} viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
              </svg>
              Query Plan
              {phase === "planning" && (
                <span className="ml-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
              )}
            </summary>
            <div className="border-t border-zinc-200 px-4 py-2 prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{planText || "Planning..."}</ReactMarkdown>
              {phase === "planning" && <BlinkingCursor />}
            </div>
          </details>
        )}

        {/* Executing indicator — stays visible during executing and answering */}
        {(phase === "executing" || phase === "answering") && (
          <div className="rounded-2xl rounded-bl-sm border border-zinc-200 bg-white px-4 py-3 text-sm shadow-sm">
            <div className="flex items-center gap-1.5 text-zinc-400">
              {phase === "executing" ? (
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <svg className="h-4 w-4 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                </svg>
              )}
              {phase === "executing" ? "Executing query..." : "Query executed"}
            </div>
          </div>
        )}

        {/* Agent answer section — markdown rendered */}
        {phase === "answering" && agentText && (
          <div className="rounded-2xl rounded-bl-sm border border-zinc-200 bg-white px-4 py-3 text-sm shadow-sm">
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{agentText}</ReactMarkdown>
              <BlinkingCursor />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function MessageList({ messages, isPending, streamingPlan = "", streamingAgent = "", streamingPhase = "idle" }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isPending, streamingPlan, streamingAgent, streamingPhase]);

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
      {isPending && streamingPhase !== "idle" && (
        <StreamingBubble
          phase={streamingPhase as "planning" | "executing" | "answering"}
          planText={streamingPlan}
          agentText={streamingAgent}
        />
      )}
      {isPending && streamingPhase === "idle" && (
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
              Connecting...
            </div>
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
