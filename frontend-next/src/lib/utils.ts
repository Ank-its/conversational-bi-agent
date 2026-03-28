/**
 * Remove inline pipe-table rows from markdown text.
 * Used when structured table_data is available to avoid duplicate rendering.
 */
export function stripPipeTables(text: string): string {
  return text
    .split("\n")
    .filter((line) => {
      const stripped = line.trim();
      if (stripped.includes("|") && !stripped.startsWith("(")) return false;
      if (
        stripped &&
        stripped.replace(/[+\-]/g, "").trim() === ""
      )
        return false;
      return true;
    })
    .join("\n")
    .trim();
}

/**
 * Create a short title from the first user message.
 */
export function truncateTitle(text: string, maxLen = 40): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + "...";
}
