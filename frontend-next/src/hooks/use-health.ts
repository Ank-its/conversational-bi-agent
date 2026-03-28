"use client";

import { useQuery } from "@tanstack/react-query";
import { healthCheck } from "@/lib/api-client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: healthCheck,
    refetchInterval: 30_000,
  });
}
