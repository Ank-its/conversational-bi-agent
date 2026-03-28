"use client";

import { useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendChat } from "@/lib/api-client";
import { useChat } from "@/providers/chat-provider";
import { truncateTitle } from "@/lib/utils";

export function useSendMessage() {
  const { getActiveSessionId, sessions, appendMessage, setTitle } = useChat();
  const abortRef = useRef<AbortController | null>(null);

  const mutation = useMutation({
    mutationFn: async (query: string) => {
      const sessionId = getActiveSessionId();
      if (!sessionId) throw new Error("No active session");

      appendMessage(sessionId, { role: "user", content: query });

      const session = sessions[sessionId];
      if (session && session.title === "New Chat") {
        setTitle(sessionId, truncateTitle(query));
      }

      const controller = new AbortController();
      abortRef.current = controller;

      const data = await sendChat(query, sessionId, controller.signal);
      abortRef.current = null;
      return { data, sessionId };
    },
    onSuccess: ({ data, sessionId }) => {
      appendMessage(sessionId, {
        role: "assistant",
        content: data.answer,
        table_data: data.table_data,
        chart_base64: data.chart?.image_base64 ?? null,
        plan: data.plan,
        refined_query: data.refined_query,
      });
    },
    onError: () => {
      abortRef.current = null;
    },
  });

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  return { ...mutation, stop };
}
