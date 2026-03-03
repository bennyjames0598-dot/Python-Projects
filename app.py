from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components

from modules.theme_manager import load_theme, save_theme, default_theme
from modules.ui_css import inject_css
from modules.data_loader import (
    normalize_columns, missing_required_columns, to_datetime_safe,
    parse_duration_days, normalize_percent_complete, wbs_level, wbs_sortkey,
    split_tokens, filter_by_resource, compute_status
)
from modules.unified_gantt import (
    build_week_buckets, build_month_buckets, build_unified_gantt
)
from modules.analytics_charts import (
    chart_tasks_by_status, chart_progress_by_project, chart_workload_by_group, chart_upcoming_milestones
)

st.set_page_config(page_title="Project Dashboard", page_icon="\U0001F4CA", layout="wide", initial_sidebar_state="expanded")

theme = load_theme()
# Initial inject
inject_css(theme)

with st.sidebar:
    st.header("\U0001F4E5 Upload")
    uploaded = st.file_uploader("Choose Excel file", type=["xlsx"]) 

# Top header (hidden in fullscreen)
show_header = not st.session_state.get('fullscr', False)
if show_header:
    c1, c2 = st.columns([1.2, 5.0], vertical_alignment="center")
    with c1:
        try:
            st.image("assets/logo.png", width=160)
        except Exception:
            st.markdown(f"<div style='color:{theme['ACCENT_BLUE']}; font-weight:900; font-size:22px;'>smartstream</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<h1 class='title-h1'>Project Dashboard</h1>", unsafe_allow_html=True)

if not uploaded:
    st.info("\U0001F448 Upload your Excel file using the sidebar to start.")
    st.stop()

from modules.data_loader import REQUIRED_COLUMNS

df_raw = pd.read_excel(uploaded, engine="openpyxl")
df_raw = normalize_columns(df_raw)
missing = missing_required_columns(df_raw)
if missing:
    st.error("❌ File format is incorrect.")
    st.write("### Missing headers:")
    st.write(missing)
    st.stop()

df = df_raw.copy()

df["Start"] = to_datetime_safe(df["Start"])  # excel serials + strings
fd = df["Finish"]
df["Finish"] = to_datetime_safe(fd)
df["Baseline Start"] = to_datetime_safe(df["Baseline Start"])
df["Baseline Finish"] = to_datetime_safe(df["Baseline Finish"])

df["% Complete"] = normalize_percent_complete(df["% Complete"])  # %, 0-1 -> 0-100

df["DurationDays"] = parse_duration_days(df["Duration"])  # numeric + '5 days'

df["WBS_Level"] = df["WBS"].apply(wbs_level)
df["WBS_SortKey"] = df["WBS"].apply(wbs_sortkey)

today = pd.Timestamp(date.today())
df["Status"] = compute_status(df, today)

# Fill empties
df["Resource Names"] = df["Resource Names"].fillna("")
df["Group name"] = df["Group name"].fillna("(Blank)")
df["Project Name"] = df["Project Name"].fillna("(Blank)")

# Sidebar: Filters + View + Theme + Chart colors
with st.sidebar:
    st.divider(); st.header("\U0001F50E Filters")
    projects = sorted(df["Project Name"].unique().tolist())
    owners = sorted(df["Group name"].unique().tolist())
    pc_vals = sorted(df["Parent/Child"].unique().tolist())
    statuses = ["Completed", "In progress", "Not started", "Overdue", "Unknown"]
    resource_tokens = sorted({t for v in df["Resource Names"].tolist() for t in split_tokens(v)})

    sel_projects = st.multiselect("Project Name", projects, default=projects)
    sel_owners = st.multiselect("Owner (Group name)", owners, default=owners)
    sel_status = st.multiselect("Status", statuses, default=statuses)
    sel_pc = st.multiselect("Parent/Child", pc_vals, default=pc_vals)
    sel_resources = st.multiselect("Resource Names", resource_tokens, default=[])

    st.divider(); st.header("\U0001F5D3\ufe0f View")
    view_mode = st.radio("Gantt view", ["Week", "Month"], index=0, horizontal=True)
    min_date = pd.to_datetime(df["Start"].min()).date() if pd.notna(df["Start"].min()) else date.today()
    max_date = pd.to_datetime(df["Finish"].max()).date() if pd.notna(df["Finish"].max()) else date.today()
    date_range = st.date_input("Date Range", value=(min_date, max_date))

    st.divider(); st.header("\U0001F3A8 Theme (Save/Load)")
    theme["DARK_BG"] = st.color_picker("App background", theme["DARK_BG"]) or theme["DARK_BG"]
    theme["PANEL_BG"] = st.color_picker("Sidebar background", theme["PANEL_BG"]) or theme["PANEL_BG"]
    theme["CARD_BG"] = st.color_picker("Card background", theme["CARD_BG"]) or theme["CARD_BG"]
    theme["TEXT"] = st.color_picker("Font color", theme["TEXT"]) or theme["TEXT"]
    theme["MUTED"] = st.color_picker("Muted color", theme["MUTED"]) or theme["MUTED"]
    theme["ACCENT_BLUE"] = st.color_picker("Accent color", theme["ACCENT_BLUE"]) or theme["ACCENT_BLUE"]

    st.write("Grid & Separators (RGBA inputs)")
    theme["BORDER"] = st.text_input("Border RGBA", theme["BORDER"]) or theme["BORDER"]
    theme["GRID_DAILY"] = st.text_input("Daily grid RGBA", theme["GRID_DAILY"]) or theme["GRID_DAILY"]
    theme["GRID_WEEKLY"] = st.text_input("Weekly separator RGBA", theme["GRID_WEEKLY"]) or theme["GRID_WEEKLY"]
    theme["EMPTY_WEEKDAY"] = st.color_picker("Empty weekday cell", theme["EMPTY_WEEKDAY"]) or theme["EMPTY_WEEKDAY"]
    theme["EMPTY_WEEKEND"] = st.color_picker("Empty weekend cell", theme["EMPTY_WEEKEND"]) or theme["EMPTY_WEEKEND"]

    st.header("\U0001F3A8 Charts Colors (overrides)")
    theme["CHART_BG"] = st.color_picker("Timeline background", theme["CHART_BG"]) or theme["CHART_BG"]
    theme["TABLE_BG"] = st.color_picker("Table (left grid) background", theme["TABLE_BG"]) or theme["TABLE_BG"]
    theme["HEADER_TEXT"] = st.color_picker("Header text color", theme["HEADER_TEXT"]) or theme["HEADER_TEXT"]
    theme["AXIS_TEXT"] = st.color_picker("Axis label color", theme["AXIS_TEXT"]) or theme["AXIS_TEXT"]

    st.write("Status colors")
    for k in list(theme["STATUS_COLORS"].keys()):
        theme["STATUS_COLORS"][k] = st.color_picker(k, theme["STATUS_COLORS"][k]) or theme["STATUS_COLORS"][k]

    default_path = st.text_input("Settings file path (JSON)", value="theme.json")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("\U0001F4BE Save Settings", use_container_width=True):
            save_theme(theme, default_path); st.toast(f"Saved to {default_path}")
    with c2:
        if st.button("\U0001F4C2 Load Settings", use_container_width=True):
            theme = load_theme(default_path); st.toast(f"Loaded from {default_path}")
    with c3:
        if st.button("♻️ Reset Defaults", use_container_width=True):
            theme = default_theme(); st.toast("Theme reset (not saved yet)")

# Re-inject with latest theme values so background applies globally
inject_css(theme)

# Apply filters
f = df.copy()
if sel_projects: f = f[f["Project Name"].isin(sel_projects)]
if sel_owners:   f = f[f["Group name"].isin(sel_owners)]
if sel_status:   f = f[f["Status"].isin(sel_status)]
if sel_pc:       f = f[f["Parent/Child"].isin(sel_pc)]
if sel_resources: f = filter_by_resource(f, sel_resources)

x_start = pd.Timestamp(date_range[0]); x_end = pd.Timestamp(date_range[1])
f = f[(f["Finish"] >= x_start) & (f["Start"] <= x_end)]

if f.empty:
    st.warning("No tasks match the selected filters / date range."); st.stop()

# Sort & prepare
dfp = f.copy().sort_values(["Project Name", "WBS_SortKey"]).reset_index(drop=True)

# KPIs (hidden in fullscreen)
show_kpis = not st.session_state.get('fullscr', False)
if show_kpis:
    total_tasks = len(dfp)
    completed = int((dfp["Status"] == "Completed").sum())
    in_prog  = int((dfp["Status"] == "In progress").sum())
    overdue  = int((dfp["Status"] == "Overdue").sum())
    not_started = int((dfp["Status"] == "Not started").sum())
    dur_sum = dfp["DurationDays"].fillna(0).sum()
    weighted_pct = ((dfp["DurationDays"].fillna(0) * dfp["% Complete"].fillna(0)).sum() / (dur_sum if dur_sum>0 else 1))
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Total Tasks", f"{total_tasks}"); k2.metric("Completed", f"{completed}"); k3.metric("In Progress", f"{in_prog}")
    k4.metric("Overdue", f"{overdue}"); k5.metric("Not Started", f"{not_started}"); k6.metric("Weighted % Complete", f"{weighted_pct:.1f}%")
    st.markdown("---")

main_tab, analytics_tab, export_tab = st.tabs(["Gantt", "Analytics", "Export"]) 

with main_tab:
    ctrl_col, legend_col = st.columns([1.0, 1.0])
    with ctrl_col:
        wheel_zoom = st.toggle("Wheel zoom", value=False, help="Off: mouse wheel scrolls vertically to see more rows. On: wheel zooms the chart.")
        st.markdown('<div class="ctrl-strip">' \
                    '<button class="ctrl-btn" id="btnFullscreen">⛶ Fullscreen</button>' \
                    '<button class="ctrl-btn" id="btnReset">↺ Reset</button>' \
                    '</div>', unsafe_allow_html=True)
    with legend_col:
        sc = theme["STATUS_COLORS"]
        st.markdown(f'<div class="legend-row">' \
            f'<div class="legend-item"><span class="legend-swatch" style="background:{sc["Completed"]}"></span>Completed</div>' \
            f'<div class="legend-item"><span class="legend-swatch" style="background:{sc["In progress"]}"></span>In progress</div>' \
            f'<div class="legend-item"><span class="legend-swatch" style="background:{sc["Not started"]}"></span>Not started</div>' \
            f'<div class="legend-item"><span class="legend-swatch" style="background:{sc["Overdue"]}"></span>Overdue</div>' \
            f'<div class="legend-item"><span class="legend-swatch" style="background:{sc["Unknown"]}"></span>Unknown</div>' \
            f'</div>', unsafe_allow_html=True)

    if 'week_px' not in st.session_state: st.session_state['week_px'] = 120
    if 'month_px' not in st.session_state: st.session_state['month_px'] = 140
    if 'fullscr' not in st.session_state: st.session_state['fullscr'] = False

    if view_mode == "Week":
        buckets = build_week_buckets(pd.Timestamp(x_start.date()), pd.Timestamp(x_end.date()))
        colw = st.session_state['week_px']
    else:
        buckets = build_month_buckets(pd.Timestamp(x_start.date()), pd.Timestamp(x_end.date()))
        colw = st.session_state['month_px']

    rows = len(dfp); row_px = 24; header_px = 160
    fig_height = min(max(rows * row_px + header_px, 800), 3200)

    fig, total_width_px, left_grid_px = build_unified_gantt(
        dfp=dfp, buckets=buckets, theme=theme, view=view_mode,
        chart_height=fig_height, font_size=12, week_or_month_col_width=colw
    )

    html = fig.to_html(include_plotlyjs="inline", full_html=False, config={"displayModeBar": True, "scrollZoom": bool(wheel_zoom)})

    outer_max_h = 900 if not st.session_state.get('fullscr') else 1600

    components.html(
        f"""
        <div class=\"plotly-wrap\" style=\"max-height:{outer_max_h}px; overflow-y:auto;\">
          <div id=\"scrollHost\" class=\"plotly-scroll\" style=\"overflow-x:auto; overflow-y:visible;\">
            <div id=\"plotContainer\" style=\"width:{total_width_px}px; margin:0; position:relative;\">{html}</div>
          </div>
        </div>
        <script>
        (function(){{
          const host = document.getElementById('scrollHost');
          const plotDiv = host ? host.querySelector('.js-plotly-plot') : null;
          let isDown=false, startX=0, startLeft=0;
          if (host) {{
            host.addEventListener('mousedown', e=>{{ isDown=true; startX=e.pageX; startLeft=host.scrollLeft; }});
            window.addEventListener('mouseup', ()=>{{ isDown=false; }});
            host.addEventListener('mousemove', e=>{{ if(!isDown) return; host.scrollLeft = startLeft - (e.pageX - startX); }});
          }}
          const fsBtn = document.getElementById('btnFullscreen');
          const resetBtn = document.getElementById('btnReset');
          if (fsBtn) fsBtn.onclick = ()=> window.parent.postMessage({{type:'SS_FULL'}}, '*');
          if (resetBtn && plotDiv) resetBtn.onclick = ()=> {{ try {{ host.scrollLeft = 0; Plotly.relayout(plotDiv, {{'xaxis2.autorange': true}}); }} catch(e) {{ console.warn(e); }} }};
        }})();
        </script>
        """,
        height=outer_max_h + 40,
        scrolling=False,
    )

with analytics_tab:
    a1, a2 = st.columns(2)
    with a1: chart_tasks_by_status(f, theme)
    with a2: chart_progress_by_project(f, theme)
    a3, a4 = st.columns(2)
    with a3: chart_workload_by_group(f, theme)
    with a4: chart_upcoming_milestones(f, theme)

with export_tab:
    st.subheader("\U0001F4E4 Export")
    total_tasks = len(dfp)
    completed = int((dfp["Status"] == "Completed").sum())
    in_prog  = int((dfp["Status"] == "In progress").sum())
    overdue  = int((dfp["Status"] == "Overdue").sum())
    not_started = int((dfp["Status"] == "Not started").sum())
    dur_sum = dfp["DurationDays"].fillna(0).sum()
    weighted_pct = ((dfp["DurationDays"].fillna(0) * dfp["% Complete"].fillna(0)).sum() / (dur_sum if dur_sum>0 else 1))

    summary = pd.DataFrame([{
        "Total Tasks": total_tasks, "Completed": completed, "In Progress": in_prog,
        "Overdue": overdue, "Not Started": not_started, "Weighted % Complete": round(weighted_pct, 2),
        "View Mode": view_mode, "Date Range": f"{x_start.date()} to {x_end.date()}"
    }])

    all_cols = [
        "WBS", "Task Mode", "Task Name", "Parent/Child",
        "Start", "Finish", "Baseline Start", "Baseline Finish",
        "Duration", "DurationDays", "% Complete", "Status",
        "Group name", "Resource Names", "Predecessors", "WBS Predecessors", "Project Name",
        "WBS_Level", "WBS_SortKey"
    ]
    for c in all_cols:
        if c not in df.columns:
            df[c] = None

    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")
        dfp.to_excel(writer, index=False, sheet_name="Filtered_Details")
        df[all_cols].to_excel(writer, index=False, sheet_name="All_Data_With_Computed")
    st.download_button(
        label="⬇️ Download (Summary + Filtered + Full Python Data)",
        data=output.getvalue(), file_name="ProjectDashboard_Export_v5_2_3.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
