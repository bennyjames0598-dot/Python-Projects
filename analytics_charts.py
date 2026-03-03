from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st

def _status_counts(df: pd.DataFrame) -> pd.DataFrame:
    s = df["Status"].astype(str).value_counts(dropna=False)
    s = s[s > 0]
    d = s.rename_axis('Status').reset_index(name='Count')
    return d

def chart_tasks_by_status(df: pd.DataFrame, theme: dict):
    d = _status_counts(df)
    if d.empty:
        st.info("No data to show for current filters.")
        return
    fig = px.bar(d, x="Status", y="Count", color="Status",
                 color_discrete_map={
                    "Completed": theme["STATUS_COLORS"]["Completed"],
                    "In progress": theme["STATUS_COLORS"]["In progress"],
                    "Not started": theme["STATUS_COLORS"]["Not started"],
                    "Overdue": theme["STATUS_COLORS"]["Overdue"],
                    "Unknown": theme["STATUS_COLORS"]["Unknown"],
                 })
    fig.update_layout(paper_bgcolor=theme["DARK_BG"], plot_bgcolor=theme.get("CHART_BG", theme["DARK_BG"]),
                      font=dict(color=theme.get("AXIS_TEXT", theme["TEXT"])), xaxis_title="Status", yaxis_title="Tasks")
    st.plotly_chart(fig, use_container_width=True)

def chart_progress_by_project(df: pd.DataFrame, theme: dict):
    g = df.copy(); g["DurationDays"] = g["DurationDays"].fillna(0)
    if g.empty:
        st.info("No data to show for current filters.")
        return
    grp = g.groupby("Project Name", as_index=False).apply(lambda x: pd.Series({
        "Weighted % Complete": (x["DurationDays"] * x["% Complete"].fillna(0)).sum() / (x["DurationDays"].sum() or 1)
    }))
    grp = grp.sort_values("Weighted % Complete")
    fig = px.bar(grp, x="Project Name", y="Weighted % Complete", text="Weighted % Complete")
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(paper_bgcolor=theme["DARK_BG"], plot_bgcolor=theme.get("CHART_BG", theme["DARK_BG"]), font=dict(color=theme.get("AXIS_TEXT", theme["TEXT"])), xaxis_title="Project", yaxis_title="Weighted % Complete", margin=dict(t=40,b=80))
    st.plotly_chart(fig, use_container_width=True)

def chart_workload_by_group(df: pd.DataFrame, theme: dict):
    if df.empty:
        st.info("No data to show for current filters.")
        return
    s = df["Group name"].fillna("(Blank)").value_counts().reset_index(); s.columns=["Group","Tasks"]
    fig = px.bar(s, x="Tasks", y="Group", orientation='h')
    fig.update_layout(paper_bgcolor=theme["DARK_BG"], plot_bgcolor=theme.get("CHART_BG", theme["DARK_BG"]), font=dict(color=theme.get("AXIS_TEXT", theme["TEXT"])), xaxis_title="Tasks", yaxis_title="Group", margin=dict(t=40,b=40))
    st.plotly_chart(fig, use_container_width=True)

def chart_upcoming_milestones(df: pd.DataFrame, theme: dict):
    import pandas as pd
    if df.empty:
        st.info("No data to show for current filters.")
        return
    today = pd.Timestamp.today().normalize(); d7=today+pd.Timedelta(days=7); d14=today+pd.Timedelta(days=14); d30=today+pd.Timedelta(days=30)
    data = pd.DataFrame({
        "Window":["Next 7d","Next 14d","Next 30d"],
        "Tasks":[int(((df["Finish"]>=today)&(df["Finish"]<=d7)).sum()), int(((df["Finish"]>d7)&(df["Finish"]<=d14)).sum()), int(((df["Finish"]>d14)&(df["Finish"]<=d30)).sum())]
    })
    fig = px.bar(data, x="Window", y="Tasks")
    fig.update_layout(paper_bgcolor=theme["DARK_BG"], plot_bgcolor=theme.get("CHART_BG", theme["DARK_BG"]), font=dict(color=theme.get("AXIS_TEXT", theme["TEXT"])), xaxis_title="", yaxis_title="Tasks Ending in Window", margin=dict(t=40,b=40))
    st.plotly_chart(fig, use_container_width=True)
