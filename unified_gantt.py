from __future__ import annotations
from typing import Tuple
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# helpers for buckets

def iso_week_start(d: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(d.date()) - pd.Timedelta(days=d.weekday())

def iso_week_end(d: pd.Timestamp) -> pd.Timestamp:
    return iso_week_start(d) + pd.Timedelta(days=6)

def build_week_buckets(range_start: pd.Timestamp, range_end: pd.Timestamp):
    buckets = []
    start = pd.Timestamp(range_start.date()); end = pd.Timestamp(range_end.date())
    cur = iso_week_start(start); end_limit = iso_week_end(end)
    while cur <= end_limit:
        wk_start = cur; wk_end = cur + pd.Timedelta(days=6)
        clip_start = max(wk_start, start); clip_end = min(wk_end, end)
        iso_year, iso_week, _ = wk_start.isocalendar()
        if clip_start.month == clip_end.month:
            line2 = f"{clip_start.day:d}–{clip_end.day:d} {clip_start.strftime('%b')}"
        else:
            line2 = f"{clip_start.day:d} {clip_start.strftime('%b')}–{clip_end.day:d} {clip_end.strftime('%b')}"
        label = f"WEEK {int(iso_week)}<br>{line2}"; key = f"{iso_year}-W{int(iso_week):02d}"
        buckets.append({"key": key, "start": clip_start, "end": clip_end, "label": label})
        cur += pd.Timedelta(days=7)
    return buckets

def build_month_buckets(range_start: pd.Timestamp, range_end: pd.Timestamp):
    buckets = []
    start = pd.Timestamp(range_start.year, range_start.month, 1)
    end = pd.Timestamp(range_end.year, range_end.month, 1)
    cur = start
    while cur <= end:
        next_month = (cur + pd.offsets.MonthBegin(1))
        month_end = next_month - pd.Timedelta(days=1)
        clip_start = max(cur, pd.Timestamp(range_start.date()))
        clip_end = min(month_end, pd.Timestamp(range_end.date()))
        key = cur.strftime('%Y-%m'); label = cur.strftime('%b %Y')
        buckets.append({"key": key, "start": clip_start, "end": clip_end, "label": label})
        cur = next_month
    return buckets

def discrete_colorscale(theme: dict):
    cmap = {0: theme["EMPTY_WEEKDAY"], 1: theme["EMPTY_WEEKEND"], 2: theme["STATUS_COLORS"]["Completed"],
            3: theme["STATUS_COLORS"]["In progress"], 4: theme["STATUS_COLORS"]["Not started"], 5: theme["STATUS_COLORS"]["Overdue"], 6: theme["STATUS_COLORS"]["Unknown"]}
    zmax = 6; scale = []
    for k in range(zmax+1):
        lo = k/(zmax+1); hi = (k+1)/(zmax+1)
        scale.append([lo, cmap[k]]); scale.append([hi, cmap[k]])
    return scale, zmax

LEFT_COLS = ["Project", "Group", "Task Name", "Start", "End"]


def build_unified_gantt(dfp: pd.DataFrame, buckets: list, theme: dict, view: str,
                         chart_height: int, font_size: int, week_or_month_col_width: int,
                         table_col_widths_px=(160, 140, 320, 100, 100)) -> Tuple[go.Figure, int, int]:
    # left grid text
    text_mat = []
    for _, row in dfp.iterrows():
        lvl = max(int(row.get("WBS_Level", 1)) - 1, 0)
        indent = "&nbsp;" * (3 * lvl)
        project = str(row.get("Project Name", ""))
        group = str(row.get("Group name", ""))
        task = str(row.get("Task Name", ""))
        stt = row.get("Start").strftime('%d-%b-%Y') if pd.notna(row.get("Start")) else ""
        fin = row.get("Finish").strftime('%d-%b-%Y') if pd.notna(row.get("Finish")) else ""
        text_mat.append([project, group, f"{indent}{task}", stt, fin])

    n_rows = len(text_mat)
    left_x = LEFT_COLS; left_y = list(range(n_rows))
    left_z = [[0.5 for _ in left_x] for _ in left_y]

    x_keys = [b["key"] for b in buckets]; x_labels = [b["label"] for b in buckets]

    code_map = {"Completed":2, "In progress":3, "Not started":4, "Overdue":5, "Unknown":6}
    Z = [[0 for _ in x_keys] for _ in range(n_rows)]; hover = []
    for i, row in dfp.reset_index(drop=True).iterrows():
        row_hover = []
        t_start, t_end = row["Start"], row["Finish"]
        status = row["Status"] if pd.notna(row["Status"]) else "Unknown"
        code = code_map.get(status, 6)
        for j, b in enumerate(buckets):
            overlaps = pd.notna(t_start) and pd.notna(t_end) and (t_end.date() >= b['start'].date()) and (t_start.date() <= b['end'].date())
            if overlaps: Z[i][j] = code
            row_hover.append(
                f"<b>{row['Task Name']}</b><br>Project: {row['Project Name']}<br>Group: {row['Group name']}<br>"
                f"Bucket: {b['label'].replace('<br>', ' ')}<br>Task: {row['Start'].date() if pd.notna(row['Start']) else ''} → {row['Finish'].date() if pd.notna(row['Finish']) else ''}<br>"
                f"Status: <b>{status}</b>"
            )
        hover.append(row_hover)

    colorscale, zmax = discrete_colorscale(theme)

    left_grid_px = sum(table_col_widths_px) + 4*6 + 20
    right_px = max(1, len(buckets)) * week_or_month_col_width
    total_width_px = left_grid_px + right_px + 40
    total_ratio = max(1, left_grid_px + right_px)
    col_widths = [left_grid_px/total_ratio, right_px/total_ratio]

    fig = make_subplots(rows=1, cols=2, column_widths=col_widths, shared_yaxes=True, horizontal_spacing=0.0)

    # Left pane background
    fig.add_trace(go.Heatmap(z=left_z, x=left_x, y=left_y, text=text_mat, texttemplate="%{text}",
                             textfont={"color": theme.get("HEADER_TEXT", theme["TEXT"]), "size": font_size},
                             colorscale=[[0, theme.get("TABLE_BG", theme["CARD_BG"])],[1, theme.get("TABLE_BG", theme["CARD_BG"])]], zmin=0, zmax=1,
                             hoverinfo="skip", showscale=False, xgap=1, ygap=1), row=1, col=1)

    # ALIGNMENT: make table header share baseline with top x-ticks of right pane
    yshift = int(theme.get('HEADER_ALIGN_YSHIFT', 30))
    for j, hdr in enumerate(left_x):
        fig.add_annotation(x=j, y=1.0, xref="x1", yref="paper", text=f"<b>{hdr}</b>", showarrow=False,
                           font=dict(color=theme.get('AXIS_TEXT', theme['TEXT']), size=font_size), align="left",
                           bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', yshift=yshift)

    # Right pane timeline
    fig.add_trace(go.Heatmap(z=Z, x=x_keys, y=left_y, colorscale=colorscale, zmin=0, zmax=zmax,
                             text=hover, hoverinfo="text", showscale=False, xgap=1, ygap=1), row=1, col=2)

    # Axes
    fig.update_yaxes(autorange="reversed", showticklabels=False, fixedrange=True, row=1, col=1)
    fig.update_yaxes(autorange="reversed", showticklabels=False, fixedrange=True, row=1, col=2)

    fig.update_xaxes(visible=False, row=1, col=1)
    fig.update_xaxes(tickmode="array", tickvals=x_keys, ticktext=x_labels, tickangle=0,
                     showgrid=True, gridcolor=theme["GRID_DAILY"], side='top',
                     showspikes=True, spikemode="across", spikesnap="cursor", spikecolor=theme["ACCENT_BLUE"], spikethickness=1.5,
                     row=1, col=2)

    fig.update_layout(width=total_width_px, height=chart_height, paper_bgcolor=theme["DARK_BG"], plot_bgcolor=theme.get("CHART_BG", theme["DARK_BG"]),
                      font=dict(color=theme.get("AXIS_TEXT", theme["TEXT"]), size=font_size), margin=dict(l=10, r=10, t=120, b=40),
                      hovermode="x unified", dragmode="pan")

    for key in x_keys:
        fig.add_vline(x=key, line_width=1, line_color=theme["GRID_DAILY"], row=1, col=2)

    return fig, total_width_px, left_grid_px
