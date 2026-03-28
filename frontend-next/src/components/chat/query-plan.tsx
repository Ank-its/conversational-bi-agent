"use client";

import ReactMarkdown from "react-markdown";

interface QueryPlanProps {
  plan: string;
}

export default function QueryPlan({ plan }: QueryPlanProps) {
  if (!plan) return null;

  return (
    <details className="mb-2 rounded border border-zinc-200 bg-zinc-50 text-sm">
      <summary className="cursor-pointer px-3 py-2 font-medium text-zinc-600 select-none">
        Query Plan
      </summary>
      <div className="border-t border-zinc-200 px-3 py-2 prose prose-sm max-w-none">
        <ReactMarkdown>{plan}</ReactMarkdown>
      </div>
    </details>
  );
}
