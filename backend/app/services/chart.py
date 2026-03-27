import base64
import io
import logging
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from app.config import AppConfig
from app.models.responses import ChartData

logger = logging.getLogger(__name__)


class ChartService:
    """Generates charts from query results and returns them as base64-encoded images."""

    def __init__(self, config: AppConfig):
        self._config = config

    @staticmethod
    def detect_chart_type(df: pd.DataFrame, query: str = "") -> str:
        """Auto-select chart type based on data shape and query keywords."""
        query_lower = query.lower()

        if any(kw in query_lower for kw in [
            "trend", "over time", "timeline", "hourly", "daily", "weekly",
            "by hour", "by day", "per hour", "per day",
        ]):
            return "line"
        if any(kw in query_lower for kw in ["share", "proportion", "percentage", "breakdown"]):
            return "pie" if len(df) <= 10 else "bar"
        if "distribution" in query_lower:
            return "bar"
        if any(kw in query_lower for kw in ["compare", "top", "rank", "most", "least", "highest", "lowest"]):
            return "bar"

        if len(df.columns) == 2:
            x_col = df.columns[0]
            if df[x_col].dtype in ["int64", "float64"] and len(df) > 5:
                return "line"
            if len(df) <= 6:
                return "pie"
            return "bar"

        return "bar"

    @staticmethod
    def parse_result(text: str) -> pd.DataFrame | None:
        """Try to parse agent text output into a DataFrame."""
        lines = text.strip().split("\n")

        # Pipe-separated table
        table_lines = [l for l in lines if "|" in l and not l.strip().startswith("+")]
        if len(table_lines) >= 2:
            header = [c.strip() for c in table_lines[0].split("|") if c.strip()]
            rows = []
            for line in table_lines[1:]:
                if set(line.strip().replace("|", "").replace("-", "").strip()) == set():
                    continue
                cells = [c.strip() for c in line.split("|") if c.strip()]
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

        # CSV-separated data
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

    def generate(self, df: pd.DataFrame, query: str = "", chart_type: str | None = None) -> ChartData | None:
        """Generate a chart from a DataFrame and return as base64-encoded ChartData."""
        if df is None or df.empty or len(df.columns) < 2:
            return None

        try:
            return self._generate_chart(df, query, chart_type)
        except Exception as e:
            logger.warning("Chart generation failed: %s", e)
            return None

    def _generate_chart(self, df: pd.DataFrame, query: str, chart_type: str | None) -> ChartData | None:
        """Internal chart generation logic."""
        if chart_type is None:
            chart_type = self.detect_chart_type(df, query)

        fig, ax = plt.subplots(figsize=(10, 6))

        x_col = df.columns[0]
        y_col = df.columns[1]

        plot_df = df.copy()
        if plot_df[x_col].dtype == object:
            plot_df[x_col] = plot_df[x_col].astype(str).str[:25]
        if len(plot_df) > 20:
            plot_df = plot_df.head(20)

        y_values = pd.to_numeric(plot_df[y_col], errors="coerce").fillna(0)

        # If all values are zero or negative, fall back to bar chart
        if chart_type == "pie" and (y_values <= 0).all():
            chart_type = "bar"

        if chart_type == "pie":
            # Filter out zero/negative values for pie chart
            mask = y_values > 0
            ax.pie(
                y_values[mask],
                labels=plot_df[x_col][mask],
                autopct="%1.1f%%",
                startangle=90,
            )
            ax.set_title(query[:80] if query else f"{y_col} by {x_col}")
        elif chart_type == "line":
            ax.plot(plot_df[x_col], y_values, marker="o")
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(query[:80] if query else f"{y_col} over {x_col}")
            plt.xticks(rotation=45, ha="right")
        else:
            ax.bar(range(len(plot_df)), y_values)
            ax.set_xticks(range(len(plot_df)))
            ax.set_xticklabels(plot_df[x_col], rotation=45, ha="right")
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(query[:80] if query else f"{y_col} by {x_col}")

        plt.tight_layout()

        # Encode to base64 instead of saving to file
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self._config.chart_dpi, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode("utf-8")

        safe_name = re.sub(r"[^\w\s-]", "", query[:40]).strip().replace(" ", "_") if query else "chart"
        filename = f"{safe_name}.png"

        return ChartData(chart_type=chart_type, image_base64=image_base64, filename=filename)
