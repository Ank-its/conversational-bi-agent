import {
  API_BASE_URL,
  CHAT_TIMEOUT,
  DEFAULT_TIMEOUT,
} from "./constants";
import type {
  ChatResponse,
  HealthResponse,
  NewChatResponse,
  SchemaResponse,
  ChatHistoryResponse,
} from "./types";

async function fetchWithTimeout<T>(
  url: string,
  options: RequestInit = {},
  timeout: number = DEFAULT_TIMEOUT,
): Promise<T> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  // If caller provides a signal, abort our controller when it fires
  if (options.signal) {
    options.signal.addEventListener("abort", () => controller.abort());
  }

  const res = await fetch(url, { ...options, signal: controller.signal });
  clearTimeout(id);

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export function healthCheck(): Promise<HealthResponse> {
  return fetchWithTimeout<HealthResponse>(`${API_BASE_URL}/api/health`);
}

export function newChat(): Promise<NewChatResponse> {
  return fetchWithTimeout<NewChatResponse>(`${API_BASE_URL}/api/chat/new`, {
    method: "POST",
  });
}

export function sendChat(
  query: string,
  sessionId: string,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return fetchWithTimeout<ChatResponse>(
    `${API_BASE_URL}/api/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: sessionId }),
      signal,
    },
    CHAT_TIMEOUT,
  );
}

export function getChatHistory(
  sessionId: string,
): Promise<ChatHistoryResponse> {
  return fetchWithTimeout<ChatHistoryResponse>(
    `${API_BASE_URL}/api/chat/${sessionId}`,
  );
}

export function getSchema(): Promise<SchemaResponse> {
  return fetchWithTimeout<SchemaResponse>(`${API_BASE_URL}/api/schema`);
}
