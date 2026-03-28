"use client";

import { useMemo, useState } from "react";

interface DataTableProps {
  data: Record<string, unknown>[];
}

export default function DataTable({ data }: DataTableProps) {
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const columns = useMemo(() => {
    if (data.length === 0) return [];
    return Object.keys(data[0]);
  }, [data]);

  const sorted = useMemo(() => {
    if (!sortCol) return data;
    return [...data].sort((a, b) => {
      const va = a[sortCol];
      const vb = b[sortCol];
      if (va == null && vb == null) return 0;
      if (va == null) return sortAsc ? -1 : 1;
      if (vb == null) return sortAsc ? 1 : -1;
      if (typeof va === "number" && typeof vb === "number") {
        return sortAsc ? va - vb : vb - va;
      }
      const sa = String(va);
      const sb = String(vb);
      return sortAsc ? sa.localeCompare(sb) : sb.localeCompare(sa);
    });
  }, [data, sortCol, sortAsc]);

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
  };

  if (data.length === 0) return null;

  return (
    <div className="mt-2 max-h-80 overflow-auto rounded border border-zinc-200">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-zinc-100">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                onClick={() => handleSort(col)}
                className="cursor-pointer whitespace-nowrap px-3 py-2 text-left font-medium text-zinc-700 select-none hover:bg-zinc-200"
              >
                {col}
                {sortCol === col ? (sortAsc ? " ▲" : " ▼") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={i} className="border-t border-zinc-100 hover:bg-zinc-50">
              {columns.map((col) => (
                <td key={col} className="px-3 py-1.5 text-zinc-600">
                  {row[col] != null ? String(row[col]) : ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
