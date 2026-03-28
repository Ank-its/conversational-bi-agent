export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const DEFAULT_TIMEOUT = 10_000;

export const SAMPLE_QUESTIONS = [
  "What are the top 10 most ordered products?",
  "Which departments have the highest reorder rate?",
  "Show order distribution by hour of day",
  "How many users placed more than 50 orders?",
];
