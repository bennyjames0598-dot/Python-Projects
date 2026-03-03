from __future__ import annotations
import re
import pandas as pd

REQUIRED_COLUMNS = [
    "WBS", "Task Mode", "Task Name", "Duration", "Start", "Finish",
    "Baseline Start", "Baseline Finish", "Predecessors", "WBS Predecessors",
    "Resource Names", "Group name", "% Complete", "Project Name", "Parent/Child",
]

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def missing_required_columns(df: pd.DataFrame) -> list:
    present = set(df.columns)
    return [c for c in REQUIRED_COLUMNS if c not in present]

_EXCEL_EPOCH = pd.Timestamp('1899-12-30')

def _parse_excel_serial(val):
    try:
        n = float(val)
        if 1 <= n <= 60000:
            return _EXCEL_EPOCH + pd.Timedelta(days=int(n))
    except Exception:
        pass
    return pd.NaT


def to_datetime_safe(s: pd.Series) -> pd.Series:
    def _parse_one(x):
        if pd.isna(x):
            return pd.NaT
        if isinstance(x, (int, float)):
            ts = _parse_excel_serial(x)
            if pd.notna(ts):
                return ts
        try:
            ts = pd.to_datetime(x, errors='coerce', dayfirst=True)
            if pd.notna(ts):
                return ts
        except Exception:
            pass
        try:
            ts = pd.to_datetime(x, errors='coerce')
            if pd.notna(ts):
                return ts
        except Exception:
            pass
        return pd.NaT
    return s.apply(_parse_one)


def parse_duration_days(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip()
    numeric = pd.to_numeric(x, errors='coerce')
    extracted = pd.to_numeric(x.str.extract(r'(\d+)', expand=False), errors='coerce')
    return numeric.where(numeric.notna(), extracted)


def normalize_percent_complete(s: pd.Series) -> pd.Series:
    if s.dtype == object:
        s = s.astype(str).str.replace('%', '', regex=False).str.strip()
    s_num = pd.to_numeric(s, errors='coerce')
    non_na = s_num.dropna()
    if len(non_na) and non_na.between(0,1).all():
        s_num = s_num * 100
    return s_num.clip(0, 100)


def wbs_level(wbs) -> int:
    s = str(wbs).strip()
    return s.count('.') + 1 if s else 0


def wbs_sortkey(wbs, pad=3) -> str:
    parts = str(wbs).strip().split('.')
    out = []
    for p in parts:
        p = p.strip()
        if p == '':
            continue
        try:
            out.append(f"{int(float(p)):0{pad}d}")
        except Exception:
            digits = re.sub(r"\D", "", p)
            out.append(digits.zfill(pad) if digits else p)
    return '.'.join(out)


def split_tokens(val) -> list:
    if val is None or pd.isna(val):
        return []
    return [t.strip() for t in str(val).split(',') if t.strip()]


def filter_by_resource(df: pd.DataFrame, selected: list) -> pd.DataFrame:
    if not selected:
        return df
    selected_set = set(selected)
    keep = []
    for v in df['Resource Names'].fillna('').astype(str).tolist():
        tokens = set(split_tokens(v))
        keep.append(bool(tokens & selected_set))
    return df[pd.Series(keep, index=df.index)]


def compute_status(df: pd.DataFrame, today: pd.Timestamp) -> pd.Series:
    pc = df['% Complete']
    start = df['Start']
    finish = df['Finish']
    status = pd.Series('Unknown', index=df.index, dtype='object')
    status = status.mask(pc >= 100, 'Completed')
    status = status.mask((pc < 100) & (finish < today), 'Overdue')
    status = status.mask((pc < 100) & (start > today), 'Not started')
    status = status.mask((pc < 100) & (start <= today) & (finish >= today), 'In progress')
    return status


def fmt_date_display(x) -> str:
    if pd.isna(x):
        return ''
    try:
        return pd.Timestamp(x).strftime('%d-%b-%Y')
    except Exception:
        return ''
