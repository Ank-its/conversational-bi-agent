"use client";

import { useChat } from "@/providers/chat-provider";
import MessageList from "./message-list";
import ChatInput from "./chat-input";

export default function ChatArea() {
  const { activeSession, isSending, streamingPlan, streamingAgent, streamingPhase, send, stop } = useChat();

  return (
    <div className="flex flex-1 flex-col">
      <MessageList
        messages={activeSession?.messages ?? []}
        isPending={isSending}
        streamingPlan={streamingPlan}
        streamingAgent={streamingAgent}
        streamingPhase={streamingPhase}
      />
      <ChatInput onSend={send} onStop={stop} isPending={isSending} />
    </div>
  );
}
