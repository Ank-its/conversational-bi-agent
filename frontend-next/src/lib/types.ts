export interface ChartData {
  chart_type: string;
  image_base64: string;
  filename: string;
}

export interface ChatResponse {
  answer: string;
  plan: string;
  table_data: Record<string, unknown>[] | null;
  chart: ChartData | null;
  session_id: string;
  refined_query: string | null;
}

export interface HealthResponse {
  status: string;
  database: string;
  tables: number;
  total_rows: number;
}

export interface TableInfo {
  name: string;
  row_count: number;
  columns: string[];
  description: string;
}

export interface SchemaResponse {
  tables: TableInfo[];
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}

export interface NewChatResponse {
  session_id: string;
}

export interface ChatHistoryMessage {
  role: string;
  content: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatHistoryMessage[];
}

export interface StoredMessage {
  role: "user" | "assistant";
  content: string;
  table_data?: Record<string, unknown>[] | null;
  chart_base64?: string | null;
  plan?: string;
  refined_query?: string | null;
}

export interface ChatSession {
  title: string;
  messages: StoredMessage[];
}
