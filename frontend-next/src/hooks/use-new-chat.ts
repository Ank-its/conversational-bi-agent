"use client";

import { useMutation } from "@tanstack/react-query";
import { newChat } from "@/lib/api-client";
import { useChat } from "@/providers/chat-provider";

export function useNewChat() {
  const { addSession, counter } = useChat();

  return useMutation({
    mutationFn: () => newChat(),
    onSuccess: (data) => {
      addSession(data.session_id);
    },
    onError: () => {
      // Fallback: create a local session ID if backend is down
      addSession(`local_${counter + 1}`);
    },
  });
}
