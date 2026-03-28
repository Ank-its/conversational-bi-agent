"use client";

import { useEffect, useRef } from "react";
import Sidebar from "@/components/sidebar/sidebar";
import ChatArea from "@/components/chat/chat-area";
import { useNewChat } from "@/hooks/use-new-chat";
import { useChat } from "@/providers/chat-provider";

export default function Home() {
  const { activeSessionId } = useChat();
  const { mutate: createChat } = useNewChat();
  const initRef = useRef(false);

  useEffect(() => {
    if (!activeSessionId && !initRef.current) {
      initRef.current = true;
      createChat();
    }
  }, [activeSessionId, createChat]);

  return (
    <div className="flex h-full">
      <Sidebar />
      <ChatArea />
    </div>
  );
}
