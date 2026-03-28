"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { StoredMessage } from "@/lib/types";
import { stripPipeTables } from "@/lib/utils";
import QueryPlan from "./query-plan";
import DataTable from "./data-table";
import ChartImage from "./chart-image";

interface AssistantBubbleProps {
  message: StoredMessage;
}

export default function AssistantBubble({ message }: AssistantBubbleProps) {
  const hasTable = message.table_data && message.table_data.length > 0;
  const displayText = hasTable
    ? stripPipeTables(message.content)
    : message.content;

  return (
    <div className="flex items-start justify-start gap-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-lg" title="BI Agent">
        🤖
      </div>
      <div className="max-w-[85%] rounded-2xl rounded-bl-sm border border-zinc-200 bg-white px-4 py-3 text-sm shadow-sm">
        {message.refined_query && (
          <p className="mb-2 text-xs italic text-zinc-400">
            Interpreted as: {message.refined_query}
          </p>
        )}

        {message.plan && <QueryPlan plan={message.plan} />}

        {displayText && (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayText}</ReactMarkdown>
          </div>
        )}

        {hasTable && <DataTable data={message.table_data!} />}

        {message.chart_base64 && <ChartImage base64={message.chart_base64} />}
      </div>
    </div>
  );
}
