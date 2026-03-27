import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving to file
import matplotlib.pyplot as plt
import pandas as pd
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHART_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHART_DIR, exist_ok=True)


def detect_chart_type(df, query=""):
    """Auto-select chart type based on data shape and query keywords."""
    query_lower = query.lower()

    # Keyword hints
    if any(kw in query_lower for kw in ["trend", "over time", "timeline", "hourly", "daily", "weekly", "by hour", "by day", "per hour", "per day"]):
        return "line"
    if any(kw in query_lower for kw in ["share", "proportion", "percentage", "breakdown"]):
        if len(df) <= 10:
            return "pie"
        return "bar"
    if "distribution" in query_lower:
        return "bar"
    if any(kw in query_lower for kw in ["compare", "top", "rank", "most", "least", "highest", "lowest"]):
        return "bar"

    # Data shape heuristics
    if len(df.columns) == 2:
        x_col = df.columns[0]
        if df[x_col].dtype in ["int64", "float64"] and len(df) > 5:
            return "line"
        if len(df) <= 6:
            return "pie"
        return "bar"

    return "bar"


def parse_result_to_df(result_text):
    """Try to parse agent text output into a DataFrame."""
    lines = result_text.strip().split("\n")

    # Look for table-like output with | separators
    table_lines = [l for l in lines if "|" in l and not l.strip().startswith("+")]
    if len(table_lines) >= 2:
        header = [c.strip() for c in table_lines[0].split("|") if c.strip()]
        rows = []
        for line in table_lines[1:]:
            if set(line.strip().replace("|", "").replace("-", "").strip()) == set():
                continue  # separator line
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) == len(header):
                rows.append(cells)
        if rows:
            df = pd.DataFrame(rows, columns=header)
            for col in df.columns:
                try:
                    # Remove commas from numbers like "9,479,291" before converting
                    df[col] = pd.to_numeric(df[col].str.replace(",", ""))
                except (ValueError, TypeError, AttributeError):
                    pass
            return df

    # Look for comma-separated data (only if no pipe tables found)
    csv_lines = [l for l in lines if "," in l and not l.startswith("(")]
    if len(csv_lines) >= 2:
        header = [c.strip() for c in csv_lines[0].split(",")]
        rows = []
        for line in csv_lines[1:]:
            cells = [c.strip() for c in line.split(",")]
            if len(cells) == len(header):
                rows.append(cells)
        if rows:
            df = pd.DataFrame(rows, columns=header)
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col].str.replace(",", ""))
                except (ValueError, TypeError, AttributeError):
                    pass
            return df

    return None


def generate_chart(df, query="", chart_type=None):
    """Generate a chart from a DataFrame and save to file. Returns the file path."""
    if df is None or df.empty or len(df.columns) < 2:
        return None

    if chart_type is None:
        chart_type = detect_chart_type(df, query)

    fig, ax = plt.subplots(figsize=(10, 6))

    x_col = df.columns[0]
    y_col = df.columns[1]

    # Truncate long labels
    if df[x_col].dtype == object:
        df = df.copy()
        df[x_col] = df[x_col].astype(str).str[:25]

    # Limit to top 20 for readability
    if len(df) > 20:
        df = df.head(20)

    if chart_type == "pie":
        ax.pie(
            pd.to_numeric(df[y_col], errors="coerce").fillna(0),
            labels=df[x_col],
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title(query[:80] if query else f"{y_col} by {x_col}")
    elif chart_type == "line":
        ax.plot(df[x_col], pd.to_numeric(df[y_col], errors="coerce").fillna(0), marker="o")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(query[:80] if query else f"{y_col} over {x_col}")
        plt.xticks(rotation=45, ha="right")
    else:  # bar
        bars = ax.bar(range(len(df)), pd.to_numeric(df[y_col], errors="coerce").fillna(0))
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df[x_col], rotation=45, ha="right")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(query[:80] if query else f"{y_col} by {x_col}")

    plt.tight_layout()

    # Save with sanitized filename
    safe_name = re.sub(r"[^\w\s-]", "", query[:40]).strip().replace(" ", "_") if query else "chart"
    filepath = os.path.join(CHART_DIR, f"{safe_name}.png")
    fig.savefig(filepath, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return filepath
