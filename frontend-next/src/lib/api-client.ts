import {
  API_BASE_URL,
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

export interface StreamCallbacks {
  onPlanToken: (token: string) => void;
  onPlanDone?: (plan: string) => void;
  onAgentToken: (token: string) => void;
  onToolCall?: (name: string, args: string) => void;
  onToolResult?: (result: string) => void;
}

export async function streamChat(
  query: string,
  sessionId: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId }),
    signal,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: ChatResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop()!;
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const payload = JSON.parse(line.slice(6));
        switch (payload.type) {
          case "plan":
            callbacks.onPlanToken(payload.chunk);
            break;
          case "plan_done":
            callbacks.onPlanDone?.(payload.plan);
            break;
          case "agent":
            callbacks.onAgentToken(payload.chunk);
            break;
          case "tool_call":
            callbacks.onToolCall?.(payload.name, payload.args);
            break;
          case "tool_result":
            callbacks.onToolResult?.(payload.result);
            break;
          case "result":
            finalResult = payload.data;
            break;
        }
      } catch {
        // skip malformed lines
      }
    }
  }

  if (!finalResult) throw new Error("No result received from stream");
  return finalResult;
}
