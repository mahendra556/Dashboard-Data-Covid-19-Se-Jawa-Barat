from __future__ import annotations

import io
import json
import logging
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

APP_TITLE = "Penyebaran COVID-19 Provinsi Jawa Barat"
SUBTITLE = "Ringkasan data historis COVID-19 Jawa Barat"
SOURCE_URL = "https://raw.githubusercontent.com/zakiego/dataset-sebaran-covid19goid/main/provinsi/JAWA_BARAT.csv"
SOURCE_REPO = "https://github.com/zakiego/dataset-sebaran-covid19goid"
DATA_DIR = Path(__file__).parent / "data"
LOCAL_CSV = DATA_DIR / "jawa_barat.csv"
LOCAL_META = DATA_DIR / "jawa_barat_metadata.json"
LOGO_PATH = Path(__file__).parent / "assets" / "lambang-jawa-barat.png"

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("covid_dashboard")

st.set_page_config(page_title=APP_TITLE, page_icon="🩺", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------- Theme and session state ----------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "Terang"
if "show_onboarding" not in st.session_state:
    st.session_state.show_onboarding = True

theme_choice = st.session_state.theme
dark = theme_choice == "Gelap"
BG = "#0B1220" if dark else "#F1F5F9"
CARD = "#111C2E" if dark else "#FFFFFF"
TEXT = "#E5E7EB" if dark else "#0F172A"
MUTED = "#A7B0C0" if dark else "#475569"
BORDER = "#243247" if dark else "#CBD5E1"
PRIMARY = "#2563EB" if dark else "#1D4ED8"
INFO_BG = "#142D4E" if dark else "#E7F2FF"
INFO_TEXT = "#D6E8FF" if dark else "#183B64"
INFO_BORDER = "#27496E" if dark else "#B8D5F2"
WARNING_BG = "#3A2D12" if dark else "#FFF7DF"
WARNING_TEXT = "#FDE68A" if dark else "#5C4310"
WARNING_BORDER = "#7A5A1B" if dark else "#E7C86A"
ERROR_BG = "#451F26" if dark else "#FFF0F0"
ERROR_TEXT = "#FECACA" if dark else "#7F1D1D"
ERROR_BORDER = "#7F2935" if dark else "#F1B3B3"
SUCCESS_BG = "#153829" if dark else "#EAF8EF"
SUCCESS_TEXT = "#BBF7D0" if dark else "#14532D"
SUCCESS_BORDER = "#286344" if dark else "#B8E2C5"

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{ background: {BG}; }}
[data-testid="stMain"] {{ color: {TEXT}; }}
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] [data-testid="stMarkdownContainer"] *,
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stCaptionContainer"] *,
[data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stWidgetLabel"] *,
[data-testid="stMain"] [data-testid="stRadioOption"],
[data-testid="stMain"] [data-testid="stRadioOption"] *,
[data-testid="stMain"] [data-testid="stMetricLabel"],
[data-testid="stMain"] [data-testid="stMetricLabel"] *,
[data-testid="stMain"] [data-testid="stMetricValue"],
[data-testid="stMain"] [data-testid="stMetricValue"] *,
[data-testid="stMain"] [data-testid="stTabs"] button,
[data-testid="stMain"] [data-testid="stTabs"] button * {{
    color: {TEXT} !important;
    overflow-wrap: anywhere;
    word-break: normal;
}}
[data-testid="stMain"] button[kind="secondary"] {{
    color: {TEXT} !important;
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
}}
[data-testid="stMain"] button[kind="primary"] {{
    color: #FFFFFF !important;
    background: {PRIMARY} !important;
    border: 1px solid {PRIMARY} !important;
}}
[data-testid="stMain"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stMain"] [data-testid="stDateInput"] input,
[data-testid="stMain"] [data-testid="stTextInput"] input,
[data-testid="stMain"] [data-testid="stTextArea"] textarea,
[data-testid="stMain"] [data-testid="stNumberInput"] input,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSidebar"] [data-testid="stDateInput"] input,
[data-testid="stSidebar"] [data-testid="stTextInput"] input,
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea,
[data-testid="stSidebar"] [data-testid="stNumberInput"] input {{
    color: {TEXT} !important;
    background: {CARD} !important;
    border-color: {BORDER} !important;
}}
[data-testid="stSelectboxVirtualDropdown"],
[data-baseweb="popover"] [role="listbox"] {{
    color: {TEXT} !important;
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
}}
[data-testid="stSelectboxVirtualDropdown"] [role="option"],
[data-baseweb="popover"] [role="option"] {{
    color: {TEXT} !important;
    background: {CARD} !important;
}}
[data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"],
[data-baseweb="popover"] [role="option"][aria-selected="true"] {{
    color: {TEXT} !important;
    background: {BG} !important;
}}
[data-baseweb="popover"] [role="dialog"],
[data-testid="stDialog"] [role="dialog"] {{
    color: {TEXT} !important;
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
}}
[data-baseweb="popover"] [role="dialog"] *,
[data-testid="stDialog"] [role="dialog"] [data-testid="stMarkdownContainer"] * {{ color: {TEXT} !important; }}
[data-testid="stAlertContentInfo"] {{
    color: {INFO_TEXT} !important;
    background: {INFO_BG} !important;
    border: 1px solid {INFO_BORDER} !important;
    border-radius: 8px;
}}
[data-testid="stMain"] [data-testid="stAlertContentInfo"] *,
[data-testid="stMain"] [data-testid="stAlertContentInfo"] svg {{ color: {INFO_TEXT} !important; fill: {INFO_TEXT} !important; }}
[data-testid="stAlertContentWarning"] {{
    color: {WARNING_TEXT} !important;
    background: {WARNING_BG} !important;
    border: 1px solid {WARNING_BORDER} !important;
    border-radius: 8px;
}}
[data-testid="stMain"] [data-testid="stAlertContentWarning"] *,
[data-testid="stMain"] [data-testid="stAlertContentWarning"] svg {{ color: {WARNING_TEXT} !important; fill: {WARNING_TEXT} !important; }}
[data-testid="stAlertContentError"] {{
    color: {ERROR_TEXT} !important;
    background: {ERROR_BG} !important;
    border: 1px solid {ERROR_BORDER} !important;
    border-radius: 8px;
}}
[data-testid="stMain"] [data-testid="stAlertContentError"] *,
[data-testid="stMain"] [data-testid="stAlertContentError"] svg {{ color: {ERROR_TEXT} !important; fill: {ERROR_TEXT} !important; }}
[data-testid="stAlertContentSuccess"] {{
    color: {SUCCESS_TEXT} !important;
    background: {SUCCESS_BG} !important;
    border: 1px solid {SUCCESS_BORDER} !important;
    border-radius: 8px;
}}
[data-testid="stMain"] [data-testid="stAlertContentSuccess"] *,
[data-testid="stMain"] [data-testid="stAlertContentSuccess"] svg {{ color: {SUCCESS_TEXT} !important; fill: {SUCCESS_TEXT} !important; }}
[data-testid="stMain"] a,
[data-testid="stSidebar"] a {{ color: {PRIMARY} !important; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ border-bottom-color: {PRIMARY} !important; }}
[data-testid="stRadioGroup"] input[type="radio"] {{ accent-color: {PRIMARY} !important; }}
[data-testid="stHeader"] {{ background: transparent; color: {TEXT}; }}
[data-testid="stHeader"] button,
[data-testid="stHeader"] button * {{ color: {TEXT} !important; }}
[data-testid="stSidebar"] {{ background: {CARD}; border-right: 1px solid {BORDER}; color: {TEXT}; }}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] [data-testid="stRadioOption"],
[data-testid="stSidebar"] [data-testid="stRadioOption"] *,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{
    color: {TEXT} !important;
    overflow-wrap: anywhere;
    word-break: normal;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
    color: {TEXT} !important;
    background: {BG} !important;
    border: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary * {{
    color: {TEXT} !important;
}}
[data-testid="stSidebar"] button[kind="secondary"] {{
    color: {TEXT} !important;
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] button[kind="secondary"] *,
[data-testid="stSidebar"] button[kind="secondary"] p {{
    color: {TEXT} !important;
}}
[data-testid="stSidebar"] [data-testid="stPopoverButton"] {{
    width: 44px !important;
    min-width: 44px !important;
    height: 44px !important;
    padding: 0 !important;
}}
[data-testid="stSidebar"] [data-testid="stPopoverButton"] > div > div:first-child {{
    justify-content: center;
}}
[data-testid="stSidebar"] [data-testid="stPopoverButton"] > div > div[aria-hidden="true"],
[data-testid="stSidebar"] [data-testid="stPopoverButton"] [data-testid="stMarkdownContainer"] {{
    display: none !important;
}}
.block-container {{ padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1500px; }}
[data-testid="stMain"] h1 {{ white-space: normal; overflow-wrap: break-word; line-height: 1.15; }}
div[data-testid="stMetric"] {{ background: {CARD}; border: 1px solid {BORDER}; padding: 16px; border-radius: 14px; }}
.small-muted {{ color: {MUTED}; font-size: .88rem; }}
</style>
""", unsafe_allow_html=True)

def fmt_num(value: Any) -> str:
    if pd.isna(value):
        return "Tidak tersedia"
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)

def themed_dataframe(frame: pd.DataFrame):
    header_style = lambda values: [
        f"color: {TEXT}; background-color: {BG}; border-color: {BORDER};"
    ] * len(values)
    return frame.style.set_properties(
        **{"color": TEXT, "background-color": CARD, "border-color": BORDER}
    ).set_table_styles([
        {"selector": "thead th", "props": [("color", TEXT), ("background-color", BG), ("border-color", BORDER)]},
        {"selector": "th.col_heading", "props": [("color", TEXT), ("background-color", BG), ("border-color", BORDER)]},
        {"selector": "th.row_heading", "props": [("color", TEXT), ("background-color", BG), ("border-color", BORDER)]},
        {"selector": "th.blank", "props": [("color", TEXT), ("background-color", BG), ("border-color", BORDER)]},
        {"selector": "td", "props": [("border-color", BORDER)]},
        {"selector": "tbody tr:nth-child(even) td", "props": [("background-color", BG)]},
    ]).apply_index(header_style, axis="columns").apply_index(header_style, axis="index")

def format_month_year(value: Any) -> str:
    month_names = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    timestamp = pd.to_datetime(value)
    return f"{month_names[timestamp.month - 1]} {timestamp.year}"

def peak_label_offset(value: Any, start: date, end: date) -> int:
    span_days = max((end - start).days, 1)
    position = (pd.to_datetime(value).date() - start).days / span_days
    if position >= 0.8:
        return -100
    if position <= 0.2:
        return 100
    return 0

def chart_hover_data(frame: pd.DataFrame) -> list[list[str]]:
    dates = pd.to_datetime(frame["Tanggal"], errors="coerce").reset_index(drop=True)
    values = pd.to_numeric(frame["Nilai"], errors="coerce").reset_index(drop=True)
    details: list[list[str]] = []
    for index, value in enumerate(values):
        if index == 0 or pd.isna(value) or pd.isna(values.iloc[index - 1]):
            details.append(["Belum ada pembanding", "Belum ada pembanding"])
            continue
        elapsed_days = (dates.iloc[index] - dates.iloc[index - 1]).total_seconds() / 86400
        if elapsed_days <= 0:
            details.append(["Belum ada pembanding", "Belum ada pembanding"])
            continue
        change = float(value - values.iloc[index - 1])
        average_change = change / elapsed_days
        formatted_average = f"{average_change:+,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")
        details.append([
            f"{change:+,.0f}".replace(",", ".") + " orang",
            f"{formatted_average} orang/hari",
        ])
    return details

def safe_filename(value: str) -> str:
    value = str(value).lower().strip().replace(" ", "-")
    value = re.sub(r"[^a-z0-9_-]+", "", value)
    return value[:60] or "jawa-barat"

def normalize_name(name: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).strip().lower())

def parse_dates(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip()
    iso_dates = values.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:$|[ T])", na=False)
    parsed = pd.to_datetime(values.where(iso_dates), errors="coerce", dayfirst=False)
    parsed.loc[~iso_dates] = pd.to_datetime(values.loc[~iso_dates], errors="coerce", dayfirst=True)
    return parsed

def find_column(columns, candidates):
    normalized = {normalize_name(c): c for c in columns}
    for candidate in candidates:
        key = normalize_name(candidate)
        if key in normalized:
            return normalized[key]
    for candidate in candidates:
        key = normalize_name(candidate)
        for norm, original in normalized.items():
            if key and key in norm:
                return original
    return None

def find_exact_column(columns, candidates):
    normalized = {normalize_name(column): column for column in columns}
    for candidate in candidates:
        key = normalize_name(candidate)
        if key in normalized:
            return normalized[key]
    return None

def detect_schema(df: pd.DataFrame) -> dict:
    cols = list(df.columns)
    return {
        "date": find_column(cols, ["tanggal", "date", "waktu", "tgl"]),
        "confirmed_daily": find_exact_column(cols, ["kasus", "kasus_baru", "confirmed_daily", "new_cases"]),
        "recovered_daily": find_exact_column(cols, ["sembuh", "sembuh_harian", "recovered_daily", "new_recovered"]),
        "deaths_daily": find_exact_column(cols, ["meninggal", "meninggal_harian", "deaths_daily", "new_deaths"]),
        "confirmed_cum": find_column(cols, ["akumulasi_kasus", "total_kasus", "confirmed_cumulative", "confirmed_total", "konfirmasi_total"]),
        "recovered_cum": find_column(cols, ["akumulasi_sembuh", "total_sembuh", "recovered_cumulative", "konfirmasi_sembuh"]),
        "deaths_cum": find_column(cols, ["akumulasi_meninggal", "total_meninggal", "deaths_cumulative", "konfirmasi_meninggal"]),
        "active_snapshot": find_column(cols, ["dirawat_or_isolasi", "konfirmasi_aktif", "aktif", "active_cases", "kasus_aktif"]),
        "active_cum": find_column(cols, ["akumulasi_dirawat_or_isolasi"]),
        "province": find_column(cols, ["provinsi", "province"]),
        "regency": find_column(cols, ["nama_kab_kota", "kabupaten_kota", "kabupatenkota", "kabupaten", "kota", "regency", "city"]),
        "district": find_column(cols, ["kecamatan", "district"]),
    }

def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
    return out

def attach_metadata(df: pd.DataFrame, source: str, note: str = "") -> pd.DataFrame:
    out = df.copy()
    out.attrs["source"] = source
    out.attrs["source_note"] = note
    return out

def remember_custom_date_range() -> None:
    st.session_state["custom_date_range"] = st.session_state["custom_date_range_widget"]

def reset_dashboard_filters() -> None:
    for key in [
        "indicator", "indicator_selection", "value_mode", "chart_type", "time_range_mode",
        "aggregation", "year_select", "custom_date_range_widget",
        "custom_date_range",
    ]:
        st.session_state.pop(key, None)
    st.session_state.show_onboarding = True

def reset_chart_zoom() -> None:
    st.session_state["chart_zoom_revision"] = st.session_state.get("chart_zoom_revision", 0) + 1

@st.cache_data(ttl=1800, show_spinner=False)
def download_source(url: str) -> tuple[pd.DataFrame | None, str]:
    try:
        response = requests.get(url, timeout=(5, 20))
        response.raise_for_status()
        if not response.text.strip():
            return None, "Sumber daring mengembalikan berkas kosong."
        df = pd.read_csv(io.BytesIO(response.content))
        if df.empty:
            return None, "Sumber daring tidak berisi baris data."
        return df, ""
    except Exception as exc:
        LOGGER.warning("Gagal memuat sumber utama: %s", exc)
        return None, f"Sumber daring tidak dapat dimuat ({type(exc).__name__}). Periksa koneksi atau unggah berkas CSV/Excel."

def load_local() -> tuple[pd.DataFrame | None, str]:
    if not LOCAL_CSV.exists():
        return None, ""
    try:
        df = pd.read_csv(LOCAL_CSV)
        note = ""
        if LOCAL_META.exists():
            try:
                meta = json.loads(LOCAL_META.read_text(encoding="utf-8"))
                note = str(meta.get("catatan", ""))
            except Exception:
                note = "Metadata lokal tidak dapat dibaca."
        return df, note
    except Exception as exc:
        LOGGER.warning("Gagal membaca data lokal: %s", exc)
        return None, "Berkas lokal ditemukan tetapi tidak dapat dibaca."

def save_local(df: pd.DataFrame, filename: str, source: str, note: str = "") -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(LOCAL_CSV, index=False, encoding="utf-8-sig")
    LOCAL_META.write_text(json.dumps({
        "nama_sumber": source, "nama_berkas_asli": filename, "url_sumber": SOURCE_URL if source == "Sumber utama" else "",
        "waktu_simpan": datetime.now().astimezone().isoformat(), "catatan": note
    }, ensure_ascii=False, indent=2), encoding="utf-8")

def prepare_data(raw: pd.DataFrame, mapping: dict | None = None) -> tuple[pd.DataFrame, dict, list[str]]:
    df = raw.copy()
    schema = detect_schema(df)
    if mapping:
        schema.update({k: v for k, v in mapping.items() if v})
    if schema.get("regency") in df.columns or schema.get("district") in df.columns:
        raise ValueError("Dashboard ini hanya menerima data tingkat provinsi. Dataset kabupaten/kota atau kecamatan tidak ditampilkan.")
    warnings = []
    date_col = schema.get("date")
    if not date_col or date_col not in df.columns:
        raise ValueError("Kolom tanggal tidak ditemukan. Pilih kolom tanggal pada bagian pemetaan kolom.")
    df["_tanggal"] = parse_dates(df[date_col])
    invalid_dates = int(df["_tanggal"].isna().sum())
    if invalid_dates:
        warnings.append(f"{invalid_dates} baris memiliki tanggal tidak valid dan tidak digunakan pada grafik.")
    df = df[df["_tanggal"].notna()].copy()
    if df.empty:
        raise ValueError("Tidak ada tanggal valid dalam dataset.")
    numeric_keys = [
        "confirmed_daily", "recovered_daily", "deaths_daily", "confirmed_cum",
        "recovered_cum", "deaths_cum", "active_snapshot", "active_cum",
    ]
    for key in numeric_keys:
        col = schema.get(key)
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if not any(schema.get(key) in df.columns for key in ["confirmed_cum", "recovered_cum", "deaths_cum"]):
        raise ValueError("Dataset tidak memiliki kolom total kumulatif positif, sembuh, atau meninggal yang dikenali. Dashboard ini menampilkan catatan historis kumulatif, bukan kasus baru harian.")
    # Canonical cumulative and active snapshot columns.
    for indicator, key in [("confirmed", "confirmed_cum"), ("recovered", "recovered_cum"), ("deaths", "deaths_cum")]:
        col = schema.get(key)
        df[f"_{indicator}_cum"] = pd.to_numeric(df[col], errors="coerce") if col and col in df.columns else float("nan")
    active_col = schema.get("active_cum") or schema.get("active_snapshot")
    df["_active_snapshot"] = pd.to_numeric(df[active_col], errors="coerce") if active_col and active_col in df.columns else float("nan")
    # Do not guess active case semantics if the source field is ambiguous.
    df["_wilayah"] = df[schema["regency"]].astype(str) if schema.get("regency") in df.columns else "Jawa Barat"
    df["_tingkat_wilayah"] = "Provinsi"
    df = df.sort_values("_tanggal").drop_duplicates(subset=["_tanggal", "_wilayah"], keep="last")
    for indicator, key in [
        ("confirmed", "confirmed_daily"),
        ("recovered", "recovered_daily"),
        ("deaths", "deaths_daily"),
    ]:
        col = schema.get(key)
        if col and col in df.columns:
            df[f"_{indicator}_new"] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[f"_{indicator}_new"] = df[f"_{indicator}_cum"].diff()
    return df, schema, list(dict.fromkeys(warnings))

def aggregate_series(
    df: pd.DataFrame,
    indicator: str,
    aggregation: str,
    period_start: date | None = None,
    value_mode: str = "Total kumulatif",
) -> pd.DataFrame:
    value_col = f"_{indicator}_{'new' if value_mode == 'Kasus baru' else 'cum'}"
    work = df.sort_values("_tanggal").copy()
    if work.empty:
        return pd.DataFrame(columns=["Tanggal", "Nilai"])
    if aggregation == "Per bulan":
        work["_periode"] = work["_tanggal"].dt.to_period("M")
    else:
        interval_days = {"Per hari": 1, "Per minggu (7 hari)": 7, "Per 2 minggu (14 hari)": 14}[aggregation]
        anchor = pd.Timestamp(period_start or work["_tanggal"].min().date())
        day_offsets = (work["_tanggal"].dt.normalize() - anchor).dt.days
        work["_periode"] = anchor + pd.to_timedelta((day_offsets // interval_days) * interval_days, unit="D")
    if value_col not in work or not work[value_col].notna().any():
        return pd.DataFrame(columns=["Tanggal", "Nilai"])
    work["_nilai"] = work[value_col]
    work = work.dropna(subset=["_nilai"])
    if value_mode == "Kasus baru":
        out = work.groupby("_periode", as_index=False).agg(_tanggal=("_tanggal", "max"), _nilai=("_nilai", "sum"))
    else:
        out = work.groupby("_periode", as_index=False).tail(1).sort_values("_tanggal")
    return out.rename(columns={"_tanggal": "Tanggal", "_nilai": "Nilai"})[["Tanggal", "Nilai"]]

def aggregate_status_periods(df: pd.DataFrame, aggregation: str, period_start: date) -> pd.DataFrame:
    columns = [
        "Tanggal observasi", "Positif kumulatif", "Sembuh kumulatif",
        "Meninggal kumulatif", "Masih dirawat/isolasi",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    work = df.sort_values("_tanggal").copy()
    if aggregation == "Per bulan":
        work["_periode"] = work["_tanggal"].dt.to_period("M")
    else:
        interval_days = {"Per hari": 1, "Per minggu (7 hari)": 7, "Per 2 minggu (14 hari)": 14}[aggregation]
        anchor = pd.Timestamp(period_start)
        day_offsets = (work["_tanggal"].dt.normalize() - anchor).dt.days
        work["_periode"] = anchor + pd.to_timedelta((day_offsets // interval_days) * interval_days, unit="D")

    rows = []
    for period, group in work.groupby("_periode", sort=True):
        row: dict[str, Any] = {"Tanggal observasi": group.iloc[-1]["_tanggal"]}
        for indicator, label in [
            ("confirmed", "Positif kumulatif"),
            ("recovered", "Sembuh kumulatif"),
            ("deaths", "Meninggal kumulatif"),
        ]:
            values = group[f"_{indicator}_cum"].dropna()
            row[label] = values.iloc[-1] if not values.empty else float("nan")
        active_values = group["_active_snapshot"].dropna()
        if not active_values.empty:
            row["Masih dirawat/isolasi"] = active_values.iloc[-1]
        elif all(pd.notna(row[label]) for label in ["Positif kumulatif", "Sembuh kumulatif", "Meninggal kumulatif"]):
            row["Masih dirawat/isolasi"] = (
                row["Positif kumulatif"] - row["Sembuh kumulatif"] - row["Meninggal kumulatif"]
            )
        else:
            row["Masih dirawat/isolasi"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)

def case_status_composition(frame: pd.DataFrame, schema: dict) -> tuple[pd.DataFrame, str]:
    required = ["_confirmed_cum", "_recovered_cum", "_deaths_cum"]
    snapshot = frame.dropna(subset=required).sort_values("_tanggal")
    if snapshot.empty:
        return pd.DataFrame(columns=["Status", "Jumlah"]), "Komposisi status memerlukan data kumulatif positif, sembuh, dan meninggal."

    latest = snapshot.iloc[-1]
    confirmed = float(latest["_confirmed_cum"])
    recovered = float(latest["_recovered_cum"])
    deaths = float(latest["_deaths_cum"])
    active_col = schema.get("active_cum")
    if active_col and active_col in snapshot.columns and pd.notna(latest[active_col]):
        active = float(latest[active_col])
        source_note = "Kasus aktif menggunakan nilai kumulatif dari sumber."
    else:
        active = confirmed - recovered - deaths
        source_note = "Kasus aktif dihitung sebagai positif kumulatif dikurangi sembuh dan meninggal."

    if any(value < 0 for value in (confirmed, recovered, deaths, active)):
        return pd.DataFrame(columns=["Status", "Jumlah"]), "Komposisi tidak ditampilkan karena sumber memuat nilai kumulatif negatif/tidak konsisten."
    if confirmed <= 0 or recovered + deaths + active <= 0:
        return pd.DataFrame(columns=["Status", "Jumlah"]), "Belum ada nilai kumulatif positif untuk membentuk komposisi status."

    composition = pd.DataFrame({
        "Status": ["Sembuh", "Masih dirawat/isolasi", "Meninggal"],
        "Jumlah": [recovered, active, deaths],
    })
    return composition, source_note

def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
        for name, frame in sheets.items():
            safe = frame.copy()
            # Prevent spreadsheet formula injection in text cells only.
            for col in safe.select_dtypes(include=["object", "string"]).columns:
                safe[col] = safe[col].map(lambda x: ("'" + x if isinstance(x, str) and x.startswith(("=", "+", "-", "@")) else x))
            safe.to_excel(writer, sheet_name=name[:31], index=False)
            ws = writer.sheets[name[:31]]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cells in ws.columns:
                letter = cells[0].column_letter
                max_len = min(max((len(str(c.value)) if c.value is not None else 0 for c in cells), default=10) + 2, 42)
                ws.column_dimensions[letter].width = max(12, max_len)
    return output.getvalue()

def metadata_frame(source: str, url: str, filters: dict, granularity: str, aggregation: str, rows: int, limitations: list[str], value_mode: str = "Total kumulatif") -> pd.DataFrame:
    info = {
        "nama_sumber": source, "url_sumber": url, "filter": json.dumps(filters, ensure_ascii=False),
        "granularitas_sumber": granularity, "agregasi_grafik": aggregation,
        "waktu_ekspor": datetime.now().astimezone().isoformat(), "jumlah_baris": rows,
        "keterbatasan": " | ".join(limitations) if limitations else "Tidak ada catatan tambahan.",
        "definisi_nilai": (
            "Kasus baru harian dijumlahkan dalam setiap interval; Per bulan memakai bulan kalender."
            if value_mode == "Kasus baru"
            else "Nilai kumulatif terakhir yang tersedia pada setiap interval ditampilkan."
        )
    }
    return pd.DataFrame({"metadata": list(info.keys()), "nilai": list(info.values())})

def download_panel(frame: pd.DataFrame, chart_frame: pd.DataFrame, source_label: str, source_url: str, filter_summary: str, aggregation: str, indicator: str, limitations: list[str], value_mode: str):
    st.subheader("Unduh data")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Data mentah terfilter**")
        st.caption(f"{len(frame)} baris asli dari sumber tanpa agregasi. Kolom harian dipakai pada grafik saat mode Kasus baru dipilih.")
        if frame.empty:
            st.info("Tidak ada baris yang cocok untuk diunduh.")
        else:
            raw = frame.drop(columns=[c for c in frame.columns if c.startswith("_") and c not in ["_tanggal","_wilayah"]], errors="ignore").copy()
            if "_tanggal" in raw:
                raw["tanggal_normalisasi"] = raw["_tanggal"].dt.strftime("%Y-%m-%d")
            st.download_button("Unduh mentah (CSV)", raw.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"covid_jawa-barat_{safe_filename(indicator)}_mentah.csv", mime="text/csv", key="raw_csv", help="Mengunduh baris sumber setelah filter, tanpa agregasi grafik.")
            st.download_button("Unduh mentah (Excel)", excel_bytes({"data":raw, "metadata":metadata_frame(source_label,source_url,{"ringkasan":filter_summary},"Sesuai sumber",aggregation,len(raw),limitations,value_mode), "kamus_kolom":pd.DataFrame({"kolom":raw.columns,"keterangan":["Kolom sumber atau kolom tanggal normalisasi"]*len(raw.columns)})}), file_name=f"covid_jawa-barat_{safe_filename(indicator)}_mentah.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="raw_xlsx", help="Mengunduh data mentah beserta metadata dan kamus kolom dalam Excel.")
    with c2:
        st.markdown("**Data grafik**")
        chart_export_description = "jumlah kasus baru" if value_mode == "Kasus baru" else "nilai kumulatif terakhir"
        st.caption(f"{len(chart_frame)} {chart_export_description} per interval {aggregation.lower()}.")
        if chart_frame.empty:
            st.info("Belum ada data grafik untuk diekspor.")
        else:
            chart_export = chart_frame.copy()
            chart_export["Tanggal"] = pd.to_datetime(chart_export["Tanggal"]).dt.strftime("%Y-%m-%d")
            st.download_button("Unduh grafik (CSV)", chart_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"covid_jawa-barat_{safe_filename(indicator)}_grafik.csv", mime="text/csv", key="chart_csv", help="Mengunduh angka pada grafik setelah dikelompokkan sesuai pilihan periode.")
            chart_dictionary = pd.DataFrame({
                "kolom": list(chart_export.columns),
                "keterangan": ["Tanggal observasi yang nilainya ditampilkan" if c == "Tanggal" else f"{indicator_display.get(indicator, 'Nilai')} per interval" for c in chart_export.columns],
            })
            chart_meta = metadata_frame(source_label, source_url, {"ringkasan": filter_summary}, "Provinsi/wilayah yang dipilih", aggregation, len(chart_export), limitations, value_mode)
            chart_excel = excel_bytes({"data": chart_export, "metadata": chart_meta, "kamus_kolom": chart_dictionary})
            st.download_button("Unduh grafik (Excel)", chart_excel, file_name=f"covid_jawa-barat_{safe_filename(indicator)}_grafik.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="chart_xlsx", help="Mengunduh angka grafik beserta metadata dan kamus kolom dalam Excel.")

# ---------------------------- Sidebar ----------------------------
with st.sidebar:
    st.markdown("## Filter dashboard")
    with st.expander("Waktu dan interval grafik", expanded=True):
        time_mode = st.selectbox(
            "Cakupan waktu",
            ["Seluruh periode", "Pilih tahun", "Rentang khusus"],
            key="time_range_mode",
            help="Pilih semua tanggal, satu tahun melalui kalender tahun, atau tanggal mulai dan akhir melalui kalender tanggal.",
        )
        aggregation = st.selectbox(
            "Kelompokkan data per",
            ["Per hari", "Per minggu (7 hari)", "Per 2 minggu (14 hari)", "Per bulan"],
            index=1,
            key="aggregation",
            help="Total kumulatif menampilkan catatan terakhir per interval. Kasus baru menjumlahkan angka harian dalam interval; Per bulan mengikuti bulan kalender.",
        )
        st.button(
            "Reset filter",
            width="stretch",
            on_click=reset_dashboard_filters,
            help="Mengembalikan cakupan waktu, interval, indikator, dan bentuk grafik ke pilihan awal serta membuka panduan.",
        )
        time_filter_slot = st.empty()
    st.divider()
    st.markdown("### Tampilan")
    st.radio("Tema", ["Terang", "Gelap"], key="theme", horizontal=True, help="Mengubah warna dashboard tanpa mengubah data atau hasil analisis.")
    st.caption("Kelompok 4")

# Load source in order: remote -> local -> upload
raw_df, source_note = download_source(SOURCE_URL)
source_label, source_url = "Sumber utama (CSV provinsi)", SOURCE_URL
if raw_df is None:
    raw_df, local_note = load_local()
    if raw_df is not None:
        source_label, source_url = "Data lokal tersimpan", str(LOCAL_CSV)
        source_note = local_note or source_note
if raw_df is None:
    raw_df = pd.DataFrame()
    source_label, source_url = "Belum ada dataset", ""

# ---------------------------- Header and guide dialog ----------------------------
h_logo, h1, h2 = st.columns([0.75, 5, 1], vertical_alignment="center", gap="medium")
with h_logo:
    st.image(LOGO_PATH, width=80, alt="Lambang Provinsi Jawa Barat")
with h1:
    st.title(APP_TITLE)
    st.caption(SUBTITLE)
with h2:
    if st.button("Panduan", width="stretch", help="Buka panduan fungsi kontrol, tab, grafik, dan unduhan."):
        st.session_state.show_onboarding = True


@st.dialog("Panduan dashboard", width="large", dismissible=False)
def show_dashboard_guide():
    st.write("Dashboard ini menyajikan data COVID-19 historis Provinsi Jawa Barat. Pilih total kumulatif untuk melihat jumlah terkumpul, atau kasus baru untuk melihat penambahan pada interval yang dipilih.")
    with st.expander("Filter waktu dan tampilan", expanded=True):
        st.markdown(
            "- **Cakupan waktu:** pilih seluruh periode yang tersedia, satu tahun melalui kalender tahun (tanpa memilih bulan/tanggal), atau rentang khusus melalui kalender tanggal lengkap.\n"
            "- **Kelompokkan data per:** pilih 1 hari, 7 hari, 14 hari, atau bulan kalender. Total kumulatif menampilkan catatan terakhir; kasus baru dijumlahkan di dalam interval.\n"
            "- **Tema:** mengganti tampilan terang atau gelap.\n"
            "- **Reset filter:** mengembalikan cakupan, interval, indikator, dan grafik ke pilihan awal serta membuka panduan."
        )
    with st.expander("Indikator, grafik, dan tab"):
        st.markdown(
            "- **Indikator yang dilihat:** memilih total positif, sembuh, meninggal, atau membandingkan ketiganya. Grafik akan menampilkan indikator yang dipilih.\n"
            "- **Jenis nilai:** pilih total kumulatif atau kasus baru. Kasus baru memakai kolom harian sumber jika tersedia; indikator lain dapat dihitung dari selisih total kumulatif.\n"
            "- **Jenis grafik:** memilih garis atau batang. Saat membandingkan semua indikator, grafik garis digunakan dan total meninggal memiliki sumbu kanan agar kenaikannya tetap terlihat.\n"
            "- **Informasi hover:** menunjukkan nilai pada tanggal/interval dan perubahan dari interval sebelumnya.\n"
            "- **Memperbesar grafik:** seret area grafik untuk memilih rentang. Gunakan tombol reset sumbu pada toolbar grafik untuk kembali ke seluruh rentang; zoom roda mouse dinonaktifkan agar tidak berubah tanpa sengaja.\n"
            "- **Grafik komposisi:** menunjukkan perbandingan status pada observasi terakhir yang tersedia.\n"
            "- **Ringkasan:** menampilkan grafik dan ringkasan otomatis.\n"
            "- **Tabel data:** menampilkan total kumulatif dan status aktif pada rentang terpilih.\n"
            "- **Sumber & metodologi:** memeriksa asal data, cakupan, dan cara penghitungan."
        )
    with st.expander("Dataset dan unduhan"):
        st.markdown(
            "- **Kelola dataset:** membaca CSV/Excel tingkat provinsi; pilih kolom tanggal yang benar sebelum menggunakannya.\n"
            "- **Simpan dataset lokal:** menyimpan unggahan untuk dipakai kembali pada perangkat ini.\n"
            "- **Unduh mentah:** mengunduh baris sumber terfilter tanpa agregasi grafik.\n"
            "- **Unduh grafik:** mengunduh angka setelah pengelompokan grafik diterapkan."
        )
    st.caption("Data kabupaten/kota dan kecamatan tidak ditampilkan karena sumber terverifikasi belum tersedia.")
    if st.button("Tutup panduan", type="primary", help="Menutup popup panduan dan kembali ke dashboard."):
        st.session_state.show_onboarding = False
        st.rerun()


if st.session_state.show_onboarding:
    show_dashboard_guide()

# Data management expander: uploads do not interrupt the dashboard filters
with st.expander("Kelola dataset (unggah CSV/Excel)", expanded=False):
    st.write("Unggah dataset tingkat provinsi yang memiliki sumber dan definisi kolom jelas. Data kabupaten/kota dan kecamatan tidak ditampilkan. Berkas unggahan tidak dianggap data resmi secara otomatis.")
    uploaded = st.file_uploader("Pilih berkas CSV atau Excel", type=["csv", "xlsx", "xls"], key="dataset_upload", help="Pilih dataset provinsi dalam format CSV atau Excel. Pastikan sumber dan definisi indikator dapat diverifikasi.")
    if uploaded is not None:
        try:
            uploaded_raw = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
            st.success(f"Berkas terbaca: {len(uploaded_raw)} baris dan {len(uploaded_raw.columns)} kolom.")
            st.write("Kolom terdeteksi:", list(uploaded_raw.columns))
            date_guess = find_column(uploaded_raw.columns, ["tanggal","date","waktu","tgl"])
            date_pick = st.selectbox("Kolom tanggal", ["(pilih)"] + list(uploaded_raw.columns), index=(list(uploaded_raw.columns).index(date_guess)+1 if date_guess in uploaded_raw.columns else 0), key="upload_date_col", help="Pilih kolom yang berisi tanggal observasi agar data dapat diproses.")
            save_upload = st.checkbox("Simpan dataset ini sebagai data lokal untuk penggunaan berikutnya", value=False, help="Menyimpan salinan dataset pada folder data aplikasi di perangkat ini.")
            if st.button("Gunakan dataset unggahan", help="Memakai file yang dipilih sebagai sumber dashboard."):
                if date_pick == "(pilih)":
                    st.error("Pilih kolom tanggal sebelum menggunakan dataset.")
                else:
                    st.session_state["uploaded_dataset_bytes"] = uploaded.getvalue()
                    st.session_state["uploaded_dataset_name"] = uploaded.name
                    st.session_state["uploaded_date_col"] = date_pick
                    if save_upload:
                        save_local(uploaded_raw, uploaded.name, "Unggahan pengguna", "Dataset lokal berasal dari unggahan pengguna; verifikasi sumber dan definisi kolom.")
                    st.success("Dataset dipilih. Dashboard akan memuat ulang dengan berkas tersebut.")
                    st.rerun()
        except Exception as exc:
            st.error(f"Berkas tidak dapat dibaca. Periksa format dan isi berkas. Detail: {type(exc).__name__}")

if "uploaded_dataset_bytes" in st.session_state:
    try:
        raw_df = pd.read_csv(io.BytesIO(st.session_state["uploaded_dataset_bytes"])) if st.session_state["uploaded_dataset_name"].lower().endswith(".csv") else pd.read_excel(io.BytesIO(st.session_state["uploaded_dataset_bytes"]))
        source_label, source_url = f"Unggahan: {st.session_state['uploaded_dataset_name']}", ""
        source_note = "Data unggahan pengguna; definisi indikator perlu diverifikasi."
    except Exception:
        st.warning("Dataset unggahan tidak dapat dibaca lagi. Muat ulang berkas.")
        raw_df = pd.DataFrame()

if raw_df.empty:
    st.warning(source_note or "Dataset utama belum tersedia.")
    st.info("Dashboard belum dapat menghitung KPI atau grafik karena belum ada dataset valid. Buka **Kelola dataset (unggah CSV/Excel)** untuk mengunggah berkas nyata. Tidak dibuatkan data contoh palsu.")
    st.markdown(f"Sumber yang dicoba: [{SOURCE_URL}]({SOURCE_URL})")
    st.stop()

try:
    mapping = {"date": st.session_state.get("uploaded_date_col")} if st.session_state.get("uploaded_date_col") else None
    df, schema, data_warnings = prepare_data(raw_df, mapping)
except Exception as exc:
    st.error(f"Dataset belum dapat diproses: {exc}")
    st.caption("Pastikan ada kolom tanggal valid dan kolom indikator yang definisinya diketahui.")
    st.stop()

min_date, max_date = df["_tanggal"].min().date(), df["_tanggal"].max().date()
st.warning(
    f"Data historis — observasi terakhir tersedia {max_date:%d %B %Y}. "
    "Pilih total kumulatif atau kasus baru untuk melihat jenis angka yang berbeda."
)
st.caption(f"Cakupan data: Provinsi Jawa Barat • {min_date:%d %B %Y}–{max_date:%d %B %Y} • Sumber: {source_label}")

# Date controls depend on actual data coverage
if time_mode == "Pilih tahun":
    years = sorted(df["_tanggal"].dt.year.unique().tolist())
    if st.session_state.get("year_select") not in years:
        st.session_state["year_select"] = years[-1]
    with time_filter_slot.container():
        st.markdown("**Pilih tahun data**")
        st.caption("Pilih satu tahun saja; bulan dan tanggal tidak perlu dipilih.")
        with st.container(border=True):
            year_columns = st.columns(2)
            for index, year in enumerate(years):
                with year_columns[index % len(year_columns)]:
                    if st.button(
                        str(year),
                        key=f"year_choice_{year}",
                        type="primary" if year == st.session_state["year_select"] else "secondary",
                        width="stretch",
                    ):
                        st.session_state["year_select"] = year
                        st.rerun()
    chosen_year = st.session_state["year_select"]
    start_date, end_date = date(int(chosen_year), 1, 1), date(int(chosen_year), 12, 31)
elif time_mode == "Rentang khusus":
    saved_range = st.session_state.get(
        "custom_date_range_widget",
        st.session_state.get("custom_date_range", (min_date, max_date)),
    )
    if isinstance(saved_range, tuple) and len(saved_range) == 2:
        saved_start = saved_range[0] if isinstance(saved_range[0], date) else min_date
        saved_end = saved_range[1] if isinstance(saved_range[1], date) else saved_start
        saved_start = min(max(saved_start, min_date), max_date)
        saved_end = min(max(saved_end, min_date), max_date)
    else:
        saved_start = saved_end = min_date
    if saved_start > saved_end:
        saved_start, saved_end = saved_end, saved_start
    st.session_state["custom_date_range_widget"] = (saved_start, saved_end)
    with time_filter_slot.container():
        selected_range = st.date_input(
            "Kalender tanggal mulai dan akhir",
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            key="custom_date_range_widget",
            on_change=remember_custom_date_range,
            help="Pilih tanggal awal dan akhir yang ingin dianalisis.",
        )
    st.session_state["custom_date_range"] = selected_range
    if isinstance(selected_range, tuple):
        selected_dates = [value for value in selected_range if isinstance(value, date)]
        start_date = selected_dates[0] if selected_dates else min_date
        end_date = selected_dates[-1] if selected_dates else start_date
    else:
        start_date = end_date = selected_range
else:
    start_date, end_date = min_date, max_date
if start_date > end_date:
    st.warning("Tanggal mulai melewati tanggal selesai. Rentang dibalik secara otomatis.")
    start_date, end_date = end_date, start_date

filtered = df[(df["_tanggal"].dt.date >= start_date) & (df["_tanggal"].dt.date <= end_date)].copy()

# Indicator and chart controls
st.subheader("Pilih data yang ingin dilihat")
value_mode_col, indicator_col, chart_col = st.columns([1.35, 2, 1.3])
with value_mode_col.container():
    value_mode = st.selectbox(
        "Jenis nilai",
        ["Total kumulatif", "Kasus baru"],
        key="value_mode",
        help="Total kumulatif adalah jumlah sampai tanggal tersebut. Kasus baru adalah angka harian yang dijumlahkan per interval.",
    )
with indicator_col.container():
    indicator_label = st.selectbox(
        "Indikator",
        ["Positif", "Sembuh", "Meninggal", "Bandingkan semua"],
        key="indicator_selection",
        help="Memilih indikator yang akan ditampilkan pada grafik. Pilihan terakhir membandingkan total positif, sembuh, dan meninggal.",
    )
with chart_col.container():
    chart_type = st.radio(
        "Jenis grafik",
        ["Garis", "Batang"],
        horizontal=True,
        key="chart_type",
        help="Pilih garis untuk melihat perubahan total dari waktu ke waktu, atau batang untuk membandingkan antar-tanggal.",
    )
indicator_map = {"Positif": "confirmed", "Sembuh": "recovered", "Meninggal": "deaths"}
selected_indicators = list(indicator_map.values()) if indicator_label == "Bandingkan semua" else [indicator_map[indicator_label]]
indicator_display = {
    "Positif": "Total positif kumulatif",
    "Sembuh": "Total sembuh kumulatif",
    "Meninggal": "Total meninggal kumulatif",
}
if value_mode == "Kasus baru":
    indicator_display = {
        "Positif": "Kasus positif baru",
        "Sembuh": "Kasus sembuh baru",
        "Meninggal": "Kasus meninggal baru",
    }
value_description = "kasus baru" if value_mode == "Kasus baru" else "total kumulatif"
hover_change_label = "Perubahan dari interval sebelumnya" if value_mode == "Kasus baru" else "Perubahan sejak catatan sebelumnya"
hover_average_line = "" if value_mode == "Kasus baru" else "Rata-rata perubahan per hari: %{customdata[1]}<br>"
new_case_method = (
    "Angka kasus baru memakai kolom harian yang tersedia pada sumber; indikator tanpa kolom harian dihitung dari selisih total kumulatif."
)
st.info(
    "Grafik menunjukkan "
    + (f"perbandingan {value_description} positif, sembuh, dan meninggal." if indicator_label == "Bandingkan semua" else f"**{indicator_display[indicator_label]}**.")
    + (
        f" {new_case_method}"
        if value_mode == "Kasus baru"
        else " Setiap angka adalah jumlah yang tercatat sampai tanggal observasi, bukan kasus baru."
    )
)
summary = f"Jawa Barat • {start_date:%d %b %Y}–{end_date:%d %b %Y} • {aggregation} • {value_description}"

# KPI values are the latest recorded snapshots in the selected date range.
st.subheader("Total pada observasi terakhir dalam rentang")
latest_observation = filtered.sort_values("_tanggal").iloc[-1] if not filtered.empty else None
latest_date_label = latest_observation["_tanggal"].strftime("%d %B %Y") if latest_observation is not None else "tidak tersedia"
st.caption(f"Nilai di bawah adalah catatan pada {latest_date_label}; bukan kasus baru harian.")
kpis = st.columns(4)
for column, (label, field, help_text) in zip(
    kpis,
    [
        ("Positif kumulatif", "_confirmed_cum", "Total positif kumulatif yang tercatat pada observasi terakhir."),
        ("Sembuh kumulatif", "_recovered_cum", "Total sembuh kumulatif yang tercatat pada observasi terakhir."),
        ("Meninggal kumulatif", "_deaths_cum", "Total meninggal kumulatif yang tercatat pada observasi terakhir."),
        ("Dirawat/isolasi", "_active_snapshot", "Jumlah yang tercatat masih dirawat atau isolasi pada observasi terakhir."),
    ],
):
    with column:
        value = latest_observation[field] if latest_observation is not None else None
        st.metric(label, fmt_num(value) if pd.notna(value) else "N/A", help=help_text)

# Chart data, use same processing path for table/download
ind_for_chart = selected_indicators[0]
chart_frame = aggregate_series(filtered, ind_for_chart, aggregation, start_date, value_mode)
chart_frame = chart_frame[(pd.to_datetime(chart_frame["Tanggal"]).dt.date >= start_date) & (pd.to_datetime(chart_frame["Tanggal"]).dt.date <= end_date)] if not chart_frame.empty else chart_frame
period_status = aggregate_status_periods(filtered, aggregation, start_date)
status_composition, composition_note = case_status_composition(filtered, schema)
tab_summary, tab_data, tab_sources = st.tabs(["Ringkasan", "Tabel data", "Sumber & metodologi"])
with tab_summary:
    peak_details: list[tuple[str, pd.Series]] = []
    comparison_frames: dict[str, pd.DataFrame] = {}
    if indicator_label == "Bandingkan semua":
        all_frames = []
        for label, ind in indicator_map.items():
            series_frame = aggregate_series(filtered, ind, aggregation, start_date, value_mode)
            if not series_frame.empty:
                series_frame["Indikator"] = indicator_display[label]
                all_frames.append(series_frame)
        if all_frames:
            plot_data = pd.concat(all_frames, ignore_index=True)
            fig = px.line(plot_data, x="Tanggal", y="Nilai", color="Indikator", template="plotly_dark" if dark else "plotly_white", color_discrete_sequence=["#0F8B8D", "#3B82F6", "#EF6A6A"])
            for peak_number, series_frame in enumerate(all_frames):
                label = series_frame["Indikator"].iloc[0]
                comparison_frames[label] = series_frame
                peak = series_frame.loc[series_frame["Nilai"].idxmax()]
                peak_details.append((label, peak))
                peak_hover = chart_hover_data(series_frame)[series_frame.index.get_loc(peak.name)]
                peak_color = {
                    indicator_display["Positif"]: "#0F8B8D",
                    indicator_display["Sembuh"]: "#3B82F6",
                    indicator_display["Meninggal"]: "#EF6A6A",
                }[label]
                peak_axis = "y2" if label == indicator_display["Meninggal"] else "y"
                fig.add_scatter(
                    x=[peak["Tanggal"]],
                    y=[peak["Nilai"]],
                    mode="markers",
                    name=f"Puncak {label}",
                    marker={"symbol": "star", "size": 13, "color": peak_color, "line": {"color": TEXT, "width": 1}},
                    showlegend=False,
                    customdata=[peak_hover],
                    yaxis=peak_axis,
                    hovertemplate=(
                        f"<b>Puncak {label}</b><br>"
                        "Tanggal observasi: %{x|%d %B %Y}<br>"
                        f"{('Kasus baru' if value_mode == 'Kasus baru' else 'Total kumulatif')}: "
                        "%{y:,.0f} orang<br>"
                        f"{hover_change_label}: "
                        "%{customdata[0]}<br>"
                        f"{hover_average_line}<extra></extra>"
                    ),
                )
            for trace in fig.data:
                if trace.name in comparison_frames:
                    trace.customdata = chart_hover_data(comparison_frames[trace.name])
                    if trace.name == indicator_display["Meninggal"]:
                        trace.yaxis = "y2"
                elif trace.name.startswith("Puncak "):
                    peak_label = trace.name[len("Puncak "):]
                    peak_frame = comparison_frames[peak_label]
                    peak_index = peak_frame["Nilai"].idxmax()
                    trace.customdata = [
                        chart_hover_data(peak_frame)[peak_frame.index.get_loc(peak_index)]
                    ]
                    if peak_label == indicator_display["Meninggal"]:
                        trace.yaxis = "y2"
        else:
            fig = None
    elif not chart_frame.empty:
        if chart_type == "Garis":
            fig = px.line(chart_frame, x="Tanggal", y="Nilai", template="plotly_dark" if dark else "plotly_white", color_discrete_sequence=["#0F8B8D"])
        else:
            fig = px.bar(chart_frame, x="Tanggal", y="Nilai", template="plotly_dark" if dark else "plotly_white", color_discrete_sequence=["#0F8B8D"])
        hover_details = chart_hover_data(chart_frame)
        fig.update_traces(
            name=indicator_display[indicator_label],
            showlegend=False,
            customdata=hover_details,
        )
        if chart_type == "Garis":
            fig.update_traces(mode="lines+markers", line={"width": 3}, marker={"size": 5})
        peak = chart_frame.loc[chart_frame["Nilai"].idxmax()]
        peak_details.append((indicator_display[indicator_label], peak))
        peak_hover = hover_details[chart_frame.index.get_loc(peak.name)]
        fig.add_scatter(
            x=[peak["Tanggal"]],
            y=[peak["Nilai"]],
            mode="markers",
            name="Puncak",
            marker={"symbol": "star", "size": 11, "color": "#F2A541", "line": {"color": TEXT, "width": 1}},
            showlegend=False,
            customdata=[peak_hover],
            hovertemplate=(
                "<b>Puncak</b><br>"
                "Tanggal observasi: %{x|%d %B %Y}<br>"
                f"{('Kasus baru' if value_mode == 'Kasus baru' else 'Total kumulatif')}: "
                "%{y:,.0f} orang<br>"
                f"{hover_change_label}: "
                "%{customdata[0]}<br>"
                f"{hover_average_line}<extra></extra>"
            ),
        )
        fig.add_annotation(
            x=peak["Tanggal"],
            y=peak["Nilai"],
            text=(
                f"<b>Kasus baru terbanyak</b><br>{format_month_year(peak['Tanggal'])}"
                if value_mode == "Kasus baru"
                else f"<b>Total kumulatif tertinggi</b><br>{format_month_year(peak['Tanggal'])}"
            ),
            showarrow=True,
            arrowhead=2,
            ax=peak_label_offset(peak["Tanggal"], start_date, end_date),
            ay=-42,
            bgcolor=CARD,
            bordercolor="#F2A541",
            borderwidth=1,
            borderpad=6,
            font={"color": TEXT, "size": 12},
        )
    else:
        fig = None
    with st.container(border=True):
        chart_title = (
            f"Perbandingan {value_description}"
            if indicator_label == "Bandingkan semua"
            else f"{indicator_display[indicator_label]} dari waktu ke waktu"
        )
        st.markdown(f"#### {chart_title}")
        st.caption(
            "Bintang menandai nilai tertinggi dalam rentang pilihan. "
            + ("Kasus baru dijumlahkan per interval; pilih Per bulan untuk membandingkan tiap bulan kalender. " if value_mode == "Kasus baru" else "Total kumulatif menunjukkan jumlah tercatat sampai tanggal observasi. ")
            + "Arahkan kursor untuk melihat tanggal dan nilai lengkap."
        )
        if fig is not None:
            plotted_values = [
                pd.to_numeric(pd.Series(trace.y), errors="coerce").dropna()
                for trace in fig.data
                if trace.y is not None and not trace.name.startswith("Puncak")
            ]
            y_max = max((values.max() for values in plotted_values if not values.empty), default=1)
            for trace in fig.data:
                if trace.name.startswith("Puncak"):
                    continue
                trace.hovertemplate = (
                    "<b>%{fullData.name}</b><br>"
                    "Tanggal observasi: %{x|%d %B %Y}<br>"
                    f"{('Kasus baru' if value_mode == 'Kasus baru' else 'Total kumulatif')}: "
                    "%{y:,.0f} orang<br>"
                    f"{hover_change_label}: "
                    "%{customdata[0]}<br>"
                    f"{hover_average_line}<extra></extra>"
                )
            if indicator_label == "Bandingkan semua":
                death_values = pd.to_numeric(
                    comparison_frames.get(indicator_display["Meninggal"], pd.DataFrame()).get(
                        "Nilai", pd.Series(dtype=float)
                    ),
                    errors="coerce",
                ).dropna()
                death_max = float(death_values.max()) if not death_values.empty else 1
            fig.update_layout(
                height=400,
                hovermode="closest",
                hoverdistance=20,
                uirevision=(
                    f"{indicator_label}|{chart_type}|{aggregation}|"
                    f"{start_date.isoformat()}|{end_date.isoformat()}|"
                    f"{st.session_state.get('chart_zoom_revision', 0)}"
                ),
                margin=dict(l=10, r=10, t=45, b=30),
                legend_title_text="Indikator",
                font={"color": TEXT},
                legend={"orientation": "h", "y": 1.12, "x": 0, "xanchor": "left", "font": {"color": TEXT}},
                hoverlabel={"font": {"color": TEXT}},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_xaxes(
                title_text="Bulan observasi" if aggregation == "Per bulan" else "Tanggal observasi",
                range=[start_date, end_date],
                autorange=False,
                minallowed=start_date,
                maxallowed=end_date,
                showgrid=False,
                zeroline=False,
                tickfont={"color": TEXT},
                title_font={"color": TEXT},
            )
            fig.update_yaxes(
                title_text=(
                    "Kasus baru per interval (positif/sembuh)"
                    if indicator_label == "Bandingkan semua" and value_mode == "Kasus baru"
                    else "Total kumulatif (positif/sembuh)"
                    if indicator_label == "Bandingkan semua"
                    else "Kasus baru per interval"
                    if value_mode == "Kasus baru"
                    else "Total kumulatif tercatat"
                ),
                rangemode="tozero",
                range=[0, max(float(y_max) * 1.22, 1)],
                minallowed=0,
                maxallowed=max(float(y_max) * 1.22, 1),
                gridcolor="#243247" if dark else "#E2E8F0",
                zeroline=False,
                tickfont={"color": TEXT},
                title_font={"color": TEXT},
            )
            if indicator_label == "Bandingkan semua":
                fig.update_layout(
                    yaxis2={
                        "title": {"text": "Kasus meninggal baru" if value_mode == "Kasus baru" else "Total meninggal kumulatif"},
                        "overlaying": "y",
                        "side": "right",
                        "rangemode": "tozero",
                        "range": [0, max(death_max * 1.22, 1)],
                        "minallowed": 0,
                        "maxallowed": max(death_max * 1.22, 1),
                        "showgrid": False,
                        "zeroline": False,
                        "automargin": True,
                        "tickfont": {"color": "#EF6A6A"},
                        "title_font": {"color": "#EF6A6A"},
                    }
                )
            fig.update_annotations(font_color=TEXT)
            st.plotly_chart(
                fig,
                width="stretch",
                key="covid_trend_chart",
                on_select="ignore",
                config={
                    "displayModeBar": True,
                    "displaylogo": False,
                    "scrollZoom": False,
                    "doubleClick": "reset",
                    "modeBarButtonsToAdd": ["resetScale2d"],
                    "responsive": True,
                },
                alt=f"Grafik {chart_title.lower()} untuk Jawa Barat pada rentang tanggal terpilih",
            )
            if peak_details:
                st.markdown("**Kasus terbanyak dalam rentang yang dipilih**" if value_mode == "Kasus baru" else "**Puncak dalam rentang yang dipilih**")
                for label, peak in peak_details:
                    peak_date = (
                        format_month_year(peak["Tanggal"])
                        if value_mode == "Kasus baru" and aggregation == "Per bulan"
                        else pd.to_datetime(peak["Tanggal"]).strftime("%d %B %Y")
                    )
                    st.caption(
                        f"{label}: **{fmt_num(peak['Nilai'])}** pada "
                        f"**{peak_date}**."
                    )
            st.button(
                "Atur ulang zoom grafik",
                key="reset_covid_chart_zoom",
                on_click=reset_chart_zoom,
                help="Mengembalikan grafik ke rentang tanggal penuh yang sedang dipilih.",
            )
            st.caption("Untuk memperbesar, pilih mode Zoom pada toolbar lalu seret area grafik. Gunakan Reset axes atau tombol di bawah grafik untuk kembali ke skala awal.")
        else:
            st.info("Belum ada nilai indikator yang dapat digambarkan untuk pilihan ini.")
    with st.container(border=True):
        st.markdown("#### Grafik bulat · Komposisi status")
        st.caption("Perbandingan proporsi status kasus pada observasi terakhir.")
        if status_composition.empty:
            st.info(composition_note)
        else:
            colors = ["#0F8B8D", "#3B82F6", "#EF6A6A"]
            total_positive = status_composition["Jumlah"].sum()
            donut = go.Figure(data=[go.Pie(
                labels=status_composition["Status"],
                values=status_composition["Jumlah"],
                hole=0.68,
                sort=False,
                direction="clockwise",
                marker={"colors": colors, "line": {"color": CARD, "width": 3}},
                textinfo="percent",
                textposition="inside",
                textfont={"color": "#FFFFFF", "size": 13},
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "%{value:,.0f} orang · %{percent}"
                    "<extra></extra>"
                ),
            )])
            donut.update_layout(
                template="plotly_dark" if dark else "plotly_white",
                height=340,
                margin=dict(l=8, r=8, t=8, b=8),
                showlegend=True,
                font={"color": TEXT},
                legend={"orientation": "h", "y": -0.12, "x": 0.5, "xanchor": "center", "font": {"size": 11, "color": TEXT}},
                hoverlabel={"font": {"color": TEXT}},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[{
                    "text": f"<b>{fmt_num(total_positive)}</b><br><span style='font-size:11px'>total status</span>",
                    "x": 0.5, "y": 0.5, "showarrow": False, "font": {"color": TEXT, "size": 16},
                }],
            )
            st.plotly_chart(
                donut,
                width="stretch",
                alt="Komposisi kasus kumulatif pada observasi terakhir dalam rentang",
            )
            status_date = (
                filtered.dropna(subset=["_confirmed_cum", "_recovered_cum", "_deaths_cum"])
                .sort_values("_tanggal")
                .iloc[-1]["_tanggal"]
                .date()
            )
            st.caption(f"Komposisi kumulatif berdasarkan observasi {status_date:%d %B %Y}. {composition_note}")
    if not period_status.empty:
        with st.container(border=True):
            st.markdown(f"#### Ringkasan kumulatif per periode · {aggregation}")
            st.caption(
                "Setiap baris berisi total kumulatif terakhir yang tersedia dalam interval tersebut; nilainya tidak dijumlahkan."
            )
            period_status_display = period_status.copy()
            period_status_display["Tanggal observasi"] = pd.to_datetime(period_status_display["Tanggal observasi"]).dt.strftime("%d %b %Y")
            for column in period_status_display.columns[1:]:
                period_status_display[column] = period_status_display[column].map(fmt_num)
            st.dataframe(
                themed_dataframe(period_status_display),
                width="stretch",
                hide_index=True,
                alt="Ringkasan nilai kumulatif terakhir pada setiap interval waktu",
            )
    if fig is not None:
        st.caption(
            f"Periode {aggregation.lower()} dihitung berurutan mulai {start_date:%d %B %Y}. "
            "Untuk setiap interval, yang ditampilkan adalah total terakhir yang tercatat."
        )
    st.subheader("Ringkasan otomatis")
    if not filtered.empty:
        st.write(f"Pada rentang **{start_date:%d %B %Y} sampai {end_date:%d %B %Y}**, dataset memuat {len(filtered)} observasi untuk **Provinsi Jawa Barat**.")
        if not chart_frame.empty:
            peak = chart_frame.loc[chart_frame["Nilai"].idxmax()]
            peak_label = (
                "Kasus positif baru terbanyak" if indicator_label == "Bandingkan semua"
                else "Kasus baru terbanyak" if value_mode == "Kasus baru"
                else "Total positif kumulatif tertinggi" if indicator_label == "Bandingkan semua"
                else "Nilai tertinggi pada grafik"
            )
            peak_date = (
                format_month_year(peak["Tanggal"])
                if value_mode == "Kasus baru" and aggregation == "Per bulan"
                else pd.to_datetime(peak["Tanggal"]).strftime("%d %B %Y")
            )
            st.write(f"{peak_label} adalah **{fmt_num(peak['Nilai'])}**, pada periode **{peak_date}**.")
        if data_warnings:
            st.info("Catatan data: " + " ".join(data_warnings))
    else:
        st.info("Tidak ada observasi pada rentang waktu yang dipilih.")
with tab_data:
    st.subheader("Data terfilter")
    if filtered.empty:
        st.info("Tidak ada baris untuk filter ini.")
    else:
        display = filtered[[
            "_tanggal", "_confirmed_cum", "_recovered_cum", "_deaths_cum", "_active_snapshot"
        ]].copy()
        display["Tanggal observasi"] = display.pop("_tanggal").dt.strftime("%Y-%m-%d")
        display = display.rename(columns={
            "_confirmed_cum": "Total positif kumulatif",
            "_recovered_cum": "Total sembuh kumulatif",
            "_deaths_cum": "Total meninggal kumulatif",
            "_active_snapshot": "Masih dirawat/isolasi",
        })
        display = display[[
            "Tanggal observasi",
            "Total positif kumulatif",
            "Total sembuh kumulatif",
            "Total meninggal kumulatif",
            "Masih dirawat/isolasi",
        ]]
        st.caption("Tabel ini hanya menampilkan total kumulatif atau jumlah status yang tercatat pada tanggal observasi; tidak menampilkan hitungan kasus baru.")
        st.dataframe(themed_dataframe(display), width="stretch", hide_index=True, alt="Total COVID-19 kumulatif per tanggal observasi")
with tab_sources:
    st.subheader("Sumber data")
    st.markdown(f"- Dataset provinsi: [{SOURCE_URL}]({SOURCE_URL})")
    st.markdown(f"- Dokumentasi repositori: [{SOURCE_REPO}]({SOURCE_REPO})")
    st.write(f"**Sumber yang sedang digunakan:** {source_label}")
    st.write(f"**Cakupan tanggal:** {min_date:%Y-%m-%d} sampai {max_date:%Y-%m-%d}")
    st.write("**Metodologi:** total kumulatif menampilkan catatan terakhir dalam interval. Kasus baru memakai kolom harian sumber jika tersedia, lalu menjumlahkan angka per interval; jika kolom harian tidak tersedia, aplikasi menghitung selisih antarcatatan kumulatif.")
    st.write("**Cakupan wilayah:** dashboard ini hanya menampilkan data tingkat Provinsi Jawa Barat. Data kabupaten/kota dan kecamatan tidak ditampilkan karena sumber terverifikasi belum tersedia.")
    if source_note:
        st.warning(source_note)
    if data_warnings:
        for warning in data_warnings:
            st.caption(f"Catatan data: {warning}")

download_panel(filtered, chart_frame, source_label, source_url, summary, aggregation, indicator_label, data_warnings, value_mode)

st.divider()
st.caption("Dashboard edukasi. Periksa sumber, cakupan tanggal, dan definisi indikator sebelum menarik kesimpulan.")
