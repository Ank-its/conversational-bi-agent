"use client";

import { useChat } from "@/providers/chat-provider";
import MessageList from "./message-list";
import ChatInput from "./chat-input";

export default function ChatArea() {
  const { activeSessionId, activeSession, isSending, sendingSessionId, streamingPlan, streamingAgent, streamingPhase, send, stop } = useChat();

  const isActiveSessionSending = isSending && sendingSessionId === activeSessionId;

  return (
    <div className="flex flex-1 flex-col">
      <MessageList
        messages={activeSession?.messages ?? []}
        isPending={isActiveSessionSending}
        streamingPlan={isActiveSessionSending ? streamingPlan : ""}
        streamingAgent={isActiveSessionSending ? streamingAgent : ""}
        streamingPhase={isActiveSessionSending ? streamingPhase : "idle"}
      />
      <ChatInput onSend={send} onStop={stop} isPending={isActiveSessionSending} />
    </div>
  );
}
