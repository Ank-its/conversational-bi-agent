"use client";

import {
  createContext,
  useCallback,
  useContext,
  useReducer,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { ChatSession, StoredMessage } from "@/lib/types";
import { sendChat } from "@/lib/api-client";
import { truncateTitle } from "@/lib/utils";

interface ChatState {
  sessions: Record<string, ChatSession>;
  activeSessionId: string | null;
  counter: number;
}

type ChatAction =
  | { type: "ADD_SESSION"; sessionId: string }
  | { type: "SET_ACTIVE"; sessionId: string }
  | { type: "APPEND_MESSAGE"; sessionId: string; message: StoredMessage }
  | { type: "SET_TITLE"; sessionId: string; title: string };

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "ADD_SESSION":
      return {
        ...state,
        sessions: {
          ...state.sessions,
          [action.sessionId]: { title: "New Chat", messages: [] },
        },
        activeSessionId: action.sessionId,
        counter: state.counter + 1,
      };
    case "SET_ACTIVE":
      return { ...state, activeSessionId: action.sessionId };
    case "APPEND_MESSAGE": {
      const session = state.sessions[action.sessionId];
      if (!session) return state;
      return {
        ...state,
        sessions: {
          ...state.sessions,
          [action.sessionId]: {
            ...session,
            messages: [...session.messages, action.message],
          },
        },
      };
    }
    case "SET_TITLE": {
      const session = state.sessions[action.sessionId];
      if (!session) return state;
      return {
        ...state,
        sessions: {
          ...state.sessions,
          [action.sessionId]: { ...session, title: action.title },
        },
      };
    }
    default:
      return state;
  }
}

interface ChatContextValue {
  sessions: Record<string, ChatSession>;
  activeSessionId: string | null;
  activeSession: ChatSession | null;
  counter: number;
  isSending: boolean;
  addSession: (sessionId: string) => void;
  setActive: (sessionId: string) => void;
  appendMessage: (sessionId: string, message: StoredMessage) => void;
  setTitle: (sessionId: string, title: string) => void;
  getActiveSessionId: () => string | null;
  send: (query: string) => void;
  stop: () => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, {
    sessions: {},
    activeSessionId: null,
    counter: 0,
  });
  const [isSending, setIsSending] = useState(false);

  const activeIdRef = useRef(state.activeSessionId);
  activeIdRef.current = state.activeSessionId;

  const sessionsRef = useRef(state.sessions);
  sessionsRef.current = state.sessions;

  const abortRef = useRef<AbortController | null>(null);

  const addSession = useCallback(
    (sessionId: string) => dispatch({ type: "ADD_SESSION", sessionId }),
    [],
  );
  const setActive = useCallback(
    (sessionId: string) => dispatch({ type: "SET_ACTIVE", sessionId }),
    [],
  );
  const appendMessage = useCallback(
    (sessionId: string, message: StoredMessage) =>
      dispatch({ type: "APPEND_MESSAGE", sessionId, message }),
    [],
  );
  const setTitleCb = useCallback(
    (sessionId: string, title: string) =>
      dispatch({ type: "SET_TITLE", sessionId, title }),
    [],
  );
  const getActiveSessionId = useCallback(() => activeIdRef.current, []);

  const send = useCallback(
    (query: string) => {
      const sessionId = activeIdRef.current;
      if (!sessionId) return;

      appendMessage(sessionId, { role: "user", content: query });

      const session = sessionsRef.current[sessionId];
      if (session && session.title === "New Chat") {
        setTitleCb(sessionId, truncateTitle(query));
      }

      const controller = new AbortController();
      abortRef.current = controller;
      setIsSending(true);

      sendChat(query, sessionId, controller.signal)
        .then((data) => {
          appendMessage(sessionId, {
            role: "assistant",
            content: data.answer,
            table_data: data.table_data,
            chart_base64: data.chart?.image_base64 ?? null,
            plan: data.plan,
            refined_query: data.refined_query,
          });
        })
        .catch(() => {
          // aborted or failed — no action needed
        })
        .finally(() => {
          abortRef.current = null;
          setIsSending(false);
        });
    },
    [appendMessage, setTitleCb],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsSending(false);
  }, []);

  const activeSession = state.activeSessionId
    ? state.sessions[state.activeSessionId] ?? null
    : null;

  return (
    <ChatContext.Provider
      value={{
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
        activeSession,
        counter: state.counter,
        isSending,
        addSession,
        setActive,
        appendMessage,
        setTitle: setTitleCb,
        getActiveSessionId,
        send,
        stop,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
