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
SUBTITLE = "Dashboard interaktif kasus COVID-19 Jawa Barat"
SOURCE_URL = "https://raw.githubusercontent.com/zakiego/dataset-sebaran-covid19goid/main/provinsi/JAWA_BARAT.csv"
SOURCE_REPO = "https://github.com/zakiego/dataset-sebaran-covid19goid"
DATA_DIR = Path(__file__).parent / "data"
LOCAL_CSV = DATA_DIR / "jawa_barat.csv"
LOCAL_META = DATA_DIR / "jawa_barat_metadata.json"
LOGO_PATH = Path(__file__).parent / "assets" / "lambang-jawa-barat.png"

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("covid_dashboard")

st.set_page_config(page_title=APP_TITLE, page_icon="🩺", layout="wide", initial_sidebar_state="expanded")

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
PRIMARY = "#60A5FA" if dark else "#1D4ED8"

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
}}
[data-testid="stMain"] button[kind="secondary"] {{
    color: {TEXT} !important;
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
}}
[data-testid="stMain"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stMain"] [data-testid="stDateInput"] input,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
    color: {TEXT} !important;
    background: {CARD} !important;
    border-color: {BORDER} !important;
}}
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

def detect_schema(df: pd.DataFrame) -> dict:
    cols = list(df.columns)
    return {
        "date": find_column(cols, ["tanggal", "date", "waktu", "tgl"]),
        "confirmed_daily": find_column(cols, ["kasus_baru", "kasus_harian", "new_cases", "konfirmasi_total_daily_growth", "kasus"]),
        "confirmed_cum": find_column(cols, ["akumulasi_kasus", "total_kasus", "confirmed_cumulative", "confirmed_total", "konfirmasi_total"]),
        "recovered_daily": find_column(cols, ["sembuh_baru", "new_recovered", "sembuh_harian", "sembuh"]),
        "recovered_cum": find_column(cols, ["akumulasi_sembuh", "total_sembuh", "recovered_cumulative", "konfirmasi_sembuh"]),
        "deaths_daily": find_column(cols, ["meninggal_baru", "new_deaths", "meninggal_harian", "meninggal"]),
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
        "indicator", "value_mode", "chart_type", "time_range_mode",
        "aggregation", "year_select", "custom_date_range_widget",
        "custom_date_range",
    ]:
        st.session_state.pop(key, None)
    st.session_state.show_onboarding = True

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
    numeric_keys = ["confirmed_daily", "confirmed_cum", "recovered_daily", "recovered_cum", "deaths_daily", "deaths_cum", "active_snapshot", "active_cum"]
    for key in numeric_keys:
        col = schema.get(key)
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Use explicit source columns only. Daily deltas are derived only from cumulative columns.
    derived_map = {
        "confirmed": ("confirmed_daily", "confirmed_cum"),
        "recovered": ("recovered_daily", "recovered_cum"),
        "deaths": ("deaths_daily", "deaths_cum"),
    }
    for indicator, (daily_key, cum_key) in derived_map.items():
        daily_col, cum_col = schema.get(daily_key), schema.get(cum_key)
        if daily_col and daily_col in df.columns:
            df[f"_{indicator}_daily"] = pd.to_numeric(df[daily_col], errors="coerce")
            df[f"_{indicator}_daily_source"] = True
        elif cum_col and cum_col in df.columns:
            sort_cols = ["_tanggal"]
            if schema.get("regency") in df.columns:
                sort_cols = [schema["regency"], "_tanggal"]
            df = df.sort_values(sort_cols)
            group_cols = [schema["regency"]] if schema.get("regency") in df.columns else []
            delta = df.groupby(group_cols, dropna=False)[cum_col].diff() if group_cols else df[cum_col].diff()
            df[f"_{indicator}_daily"] = delta
            df[f"_{indicator}_daily_source"] = False
            warnings.append(f"Nilai harian {indicator} dihitung dari selisih kumulatif; koreksi negatif dipertahankan.")
        else:
            df[f"_{indicator}_daily"] = float("nan")
            df[f"_{indicator}_daily_source"] = False
    # Canonical cumulative and active snapshot columns.
    for indicator, key in [("confirmed", "confirmed_cum"), ("recovered", "recovered_cum"), ("deaths", "deaths_cum")]:
        col = schema.get(key)
        df[f"_{indicator}_cum"] = pd.to_numeric(df[col], errors="coerce") if col and col in df.columns else float("nan")
    active_col = schema.get("active_snapshot") or schema.get("active_cum")
    df["_active_snapshot"] = pd.to_numeric(df[active_col], errors="coerce") if active_col and active_col in df.columns else float("nan")
    # Do not guess active case semantics if the source field is ambiguous.
    df["_wilayah"] = df[schema["regency"]].astype(str) if schema.get("regency") in df.columns else "Jawa Barat"
    df["_tingkat_wilayah"] = "Provinsi"
    df = df.sort_values("_tanggal").drop_duplicates(subset=["_tanggal", "_wilayah"], keep="last")
    if any((df[f"_{k}_daily"] < 0).any() for k in ["confirmed", "recovered", "deaths"]):
        warnings.append("Ditemukan perubahan harian negatif yang mungkin merupakan koreksi data. Nilai tidak diubah menjadi nol.")
    return df, schema, list(dict.fromkeys(warnings))

def aggregate_series(
    df: pd.DataFrame,
    indicator: str,
    mode: str,
    aggregation: str,
    period_start: date | None = None,
) -> pd.DataFrame:
    daily_col = f"_{indicator}_daily"
    cum_col = f"_{indicator}_cum"
    work = df.sort_values("_tanggal").copy()
    if work.empty:
        return pd.DataFrame(columns=["Tanggal", "Nilai"])
    interval_days = {"Per hari": 1, "Per minggu (7 hari)": 7, "Per 2 minggu (14 hari)": 14}[aggregation]
    anchor = pd.Timestamp(period_start or work["_tanggal"].min().date())
    day_offsets = (work["_tanggal"].dt.normalize() - anchor).dt.days
    work["_periode"] = anchor + pd.to_timedelta((day_offsets // interval_days) * interval_days, unit="D")
    if mode == "Kumulatif":
        if work[cum_col].notna().any():
            work["_nilai"] = work[cum_col]
            out = work.dropna(subset=["_nilai"]).groupby("_periode", as_index=False).tail(1).sort_values("_periode")
            return out.rename(columns={"_periode":"Tanggal", "_nilai":"Nilai"})[["Tanggal","Nilai"]]
        return pd.DataFrame(columns=["Tanggal","Nilai"])
    work["_nilai"] = work[daily_col]
    grouped = work.groupby("_periode")["_nilai"].sum(min_count=1)
    return grouped.rename_axis("Tanggal").reset_index(name="Nilai")

def aggregate_status_periods(df: pd.DataFrame, aggregation: str, period_start: date) -> pd.DataFrame:
    columns = [
        "Tanggal", "Positif baru", "Sembuh baru", "Meninggal baru",
        "Kasus aktif", "Total positif kumulatif",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    interval_days = {"Per hari": 1, "Per minggu (7 hari)": 7, "Per 2 minggu (14 hari)": 14}[aggregation]
    work = df.sort_values("_tanggal").copy()
    anchor = pd.Timestamp(period_start)
    day_offsets = (work["_tanggal"].dt.normalize() - anchor).dt.days
    work["_periode"] = anchor + pd.to_timedelta((day_offsets // interval_days) * interval_days, unit="D")

    rows = []
    for period, group in work.groupby("_periode", sort=True):
        row: dict[str, Any] = {"Tanggal": period}
        for indicator, label in [
            ("confirmed", "Positif baru"),
            ("recovered", "Sembuh baru"),
            ("deaths", "Meninggal baru"),
        ]:
            row[label] = group[f"_{indicator}_daily"].sum(min_count=1)

        snapshot = group.dropna(subset=["_confirmed_cum", "_recovered_cum", "_deaths_cum"])
        if snapshot.empty:
            row["Kasus aktif"] = float("nan")
            row["Total positif kumulatif"] = float("nan")
        else:
            latest = snapshot.iloc[-1]
            row["Total positif kumulatif"] = latest["_confirmed_cum"]
            active = latest["_active_snapshot"]
            row["Kasus aktif"] = (
                active
                if pd.notna(active)
                else latest["_confirmed_cum"] - latest["_recovered_cum"] - latest["_deaths_cum"]
            )
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

def metadata_frame(source: str, url: str, filters: dict, granularity: str, aggregation: str, rows: int, limitations: list[str]) -> pd.DataFrame:
    info = {
        "nama_sumber": source, "url_sumber": url, "filter": json.dumps(filters, ensure_ascii=False),
        "granularitas_sumber": granularity, "agregasi_grafik": aggregation,
        "waktu_ekspor": datetime.now().astimezone().isoformat(), "jumlah_baris": rows,
        "keterbatasan": " | ".join(limitations) if limitations else "Tidak ada catatan tambahan.",
        "definisi_derived": "Nilai harian turunan = selisih antarobservasi kumulatif dalam wilayah yang sama; nilai negatif dipertahankan."
    }
    return pd.DataFrame({"metadata": list(info.keys()), "nilai": list(info.values())})

def download_panel(frame: pd.DataFrame, chart_frame: pd.DataFrame, source_label: str, source_url: str, filter_summary: str, aggregation: str, indicator: str, limitations: list[str]):
    st.subheader("Unduh data")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Data mentah terfilter**")
        st.caption(f"{len(frame)} baris sumber setelah filter. Tidak diagregasi.")
        if frame.empty:
            st.info("Tidak ada baris yang cocok untuk diunduh.")
        else:
            raw = frame.drop(columns=[c for c in frame.columns if c.startswith("_") and c not in ["_tanggal","_wilayah"]], errors="ignore").copy()
            if "_tanggal" in raw:
                raw["tanggal_normalisasi"] = raw["_tanggal"].dt.strftime("%Y-%m-%d")
            st.download_button("Unduh mentah (CSV)", raw.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"covid_jawa-barat_{safe_filename(indicator)}_mentah.csv", mime="text/csv", key="raw_csv", help="Mengunduh baris sumber setelah filter, tanpa agregasi grafik.")
            st.download_button("Unduh mentah (Excel)", excel_bytes({"data":raw, "metadata":metadata_frame(source_label,source_url,{"ringkasan":filter_summary},"Sesuai sumber",aggregation,len(raw),limitations), "kamus_kolom":pd.DataFrame({"kolom":raw.columns,"keterangan":["Kolom sumber atau kolom tanggal normalisasi"]*len(raw.columns)})}), file_name=f"covid_jawa-barat_{safe_filename(indicator)}_mentah.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="raw_xlsx", help="Mengunduh data mentah beserta metadata dan kamus kolom dalam Excel.")
    with c2:
        st.markdown("**Data grafik**")
        st.caption(f"{len(chart_frame)} baris setelah agregasi {aggregation.lower()}.")
        if chart_frame.empty:
            st.info("Belum ada data grafik untuk diekspor.")
        else:
            chart_export = chart_frame.copy()
            chart_export["Tanggal"] = pd.to_datetime(chart_export["Tanggal"]).dt.strftime("%Y-%m-%d")
            st.download_button("Unduh grafik (CSV)", chart_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"covid_jawa-barat_{safe_filename(indicator)}_grafik.csv", mime="text/csv", key="chart_csv", help="Mengunduh angka pada grafik setelah dikelompokkan sesuai pilihan periode.")
            chart_dictionary = pd.DataFrame({
                "kolom": list(chart_export.columns),
                "keterangan": ["Tanggal periode grafik" if c == "Tanggal" else "Nilai indikator terpilih" for c in chart_export.columns],
            })
            chart_meta = metadata_frame(source_label, source_url, {"ringkasan": filter_summary}, "Provinsi/wilayah yang dipilih", aggregation, len(chart_export), limitations)
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
            ["Per hari", "Per minggu (7 hari)", "Per 2 minggu (14 hari)"],
            index=1,
            key="aggregation",
            help="Kasus baru dijumlahkan dalam setiap kelompok. Untuk data kumulatif, grafik memakai observasi terakhir dalam kelompok.",
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
    st.caption("by klompok 4")

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
    st.write("Dashboard ini menampilkan data COVID-19 tingkat Provinsi Jawa Barat. Bantuan singkat juga tersedia dengan mengarahkan kursor ke ikon informasi di samping kontrol.")
    with st.expander("Filter waktu dan tampilan", expanded=True):
        st.markdown(
            "- **Cakupan waktu:** pilih seluruh periode yang tersedia, satu tahun melalui kalender tahun (tanpa memilih bulan/tanggal), atau rentang khusus melalui kalender tanggal lengkap.\n"
            "- **Kelompokkan data per:** pilih 1 hari, 7 hari, atau 14 hari. Kelompok 7/14 hari dimulai dari tanggal awal cakupan yang dipilih.\n"
            "- **Kasus baru:** nilai dijumlahkan di dalam setiap kelompok waktu. **Kumulatif:** grafik memakai observasi terakhir dalam kelompok, bukan menjumlahkan total kumulatif.\n"
            "- **Tema:** mengganti tampilan terang atau gelap.\n"
            "- **Reset filter:** mengembalikan cakupan, interval, indikator, dan grafik ke pilihan awal serta membuka panduan."
        )
    with st.expander("Indikator, grafik, dan tab"):
        st.markdown(
            "- **Indikator:** memilih positif, sembuh, meninggal, atau membandingkan semuanya.\n"
            "- **Jenis nilai:** memilih kasus baru atau angka kumulatif.\n"
            "- **Bentuk grafik:** memilih garis untuk melihat tren atau batang untuk membandingkan periode.\n"
            "- **Grafik statistik:** menunjukkan perubahan kasus dari waktu ke waktu.\n"
            "- **Grafik bulat:** menunjukkan perbandingan komposisi status pada observasi terakhir.\n"
            "- **Ringkasan:** menampilkan grafik dan ringkasan otomatis.\n"
            "- **Tabel data:** menampilkan nilai sumber pada rentang terpilih.\n"
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
st.caption(f"Cakupan: Provinsi Jawa Barat • Observasi tersedia: {min_date:%d %B %Y}–{max_date:%d %B %Y} • Sumber: {source_label}")

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

# Main chart controls
st.subheader("Indikator utama")
control1, control2, control3 = st.columns([2,2,2])
with control1:
    indicator_label = st.radio("Indikator", ["Terkonfirmasi positif", "Sembuh", "Meninggal", "Semua indikator"], horizontal=False, key="indicator", help="Pilih jenis data kasus yang ingin dilihat.")
with control2:
    value_mode = st.radio("Jenis nilai", ["Kasus baru", "Kumulatif"], horizontal=False, key="value_mode", help="Kasus baru menunjukkan perubahan pada periode; kumulatif menunjukkan total tercatat hingga observasi terakhir.")
with control3:
    chart_type = st.radio("Bentuk grafik", ["Garis", "Batang"], horizontal=True, key="chart_type", help="Pilih garis untuk membaca tren atau batang untuk membandingkan nilai antarperiode.")
indicator_map = {"Terkonfirmasi positif":"confirmed", "Sembuh":"recovered", "Meninggal":"deaths"}
selected_indicators = list(indicator_map.values()) if indicator_label == "Semua indikator" else [indicator_map[indicator_label]]
mode = "Kasus baru" if value_mode == "Kasus baru" else "Kumulatif"
summary = f"Jawa Barat • {start_date:%d %b %Y}–{end_date:%d %b %Y} • {aggregation} • {mode}"
st.info(summary)

# KPI: sum daily new values, cumulative as latest snapshot, active at reference date
kpis = st.columns(4)
for i, (label, indicator) in enumerate([("Kasus positif baru","confirmed"),("Sembuh baru","recovered"),("Meninggal baru","deaths"),("Kasus aktif pada tanggal akhir","active")]):
    with kpis[i]:
        if indicator == "active":
            series = filtered["_active_snapshot"].dropna()
            val = series.iloc[-1] if len(series) else None
            st.metric(label, fmt_num(val) if val is not None else "N/A", help="Nilai snapshot aktif pada observasi terakhir dalam rentang yang dipilih.")
        else:
            series = filtered[f"_{indicator}_daily"].dropna()
            val = series.sum(min_count=1) if len(series) else None
            st.metric(label, fmt_num(val) if val is not None else "N/A", help="Jumlah nilai harian indikator ini pada rentang waktu yang dipilih.")
st.caption("Tiga KPI pertama menjumlahkan nilai harian pada rentang terpilih. Kasus aktif adalah snapshot observasi terakhir, bukan penjumlahan harian.")

# Chart data, use same processing path for table/download
ind_for_chart = selected_indicators[0]
chart_frame = aggregate_series(filtered, ind_for_chart, mode, aggregation, start_date)
chart_frame = chart_frame[(pd.to_datetime(chart_frame["Tanggal"]).dt.date >= start_date) & (pd.to_datetime(chart_frame["Tanggal"]).dt.date <= end_date)] if not chart_frame.empty else chart_frame
if not chart_frame.empty:
    chart_frame["Rata-rata 7 hari"] = chart_frame["Nilai"].rolling(7, min_periods=3).mean()
period_status = aggregate_status_periods(filtered, aggregation, start_date)
status_composition, composition_note = case_status_composition(filtered, schema)
tab_summary, tab_data, tab_sources = st.tabs(["Ringkasan", "Tabel data", "Sumber & metodologi"])
with tab_summary:
    if indicator_label == "Semua indikator":
        all_frames = []
        for label, ind in indicator_map.items():
            series_frame = aggregate_series(filtered, ind, mode, aggregation, start_date)
            if not series_frame.empty:
                series_frame["Indikator"] = label
                all_frames.append(series_frame)
        if all_frames:
            plot_data = pd.concat(all_frames, ignore_index=True)
            fig = px.line(plot_data, x="Tanggal", y="Nilai", color="Indikator", markers=False, template="plotly_dark" if dark else "plotly_white", color_discrete_sequence=["#0F8B8D", "#3B82F6", "#EF6A6A"])
        else:
            fig = None
    elif not chart_frame.empty:
        if chart_type == "Garis":
            fig = px.line(chart_frame, x="Tanggal", y="Nilai", markers=False, template="plotly_dark" if dark else "plotly_white", color_discrete_sequence=["#0F8B8D"])
            if value_mode == "Kasus baru":
                fig.add_scatter(x=chart_frame["Tanggal"], y=chart_frame["Rata-rata 7 hari"], mode="lines", name="Rata-rata 7 periode", line={"color":"#F2A541","width":2,"dash":"dot"})
        else:
            fig = px.bar(chart_frame, x="Tanggal", y="Nilai", template="plotly_dark" if dark else "plotly_white", color_discrete_sequence=["#0F8B8D"])
        peak = chart_frame.loc[chart_frame["Nilai"].idxmax()]
        fig.add_annotation(x=peak["Tanggal"], y=peak["Nilai"], text=f"Puncak: {fmt_num(peak['Nilai'])}", showarrow=True, arrowhead=2)
    else:
        fig = None
    with st.container(border=True):
        st.markdown("#### Grafik statistik · Tren kasus")
        st.caption("Perubahan kasus dari waktu ke waktu sesuai indikator dan filter yang dipilih.")
        if fig is not None:
            for trace in fig.data:
                trace.hovertemplate = (
                    "<b>%{fullData.name}</b><br>"
                    "%{x|%d %b %Y} · %{y:,.0f} orang"
                    "<extra></extra>"
                )
            fig.update_layout(
                height=420,
                hovermode="x unified",
                margin=dict(l=10, r=10, t=25, b=10),
                legend_title_text="Indikator",
                font={"color": TEXT},
                legend={"font": {"color": TEXT}},
                hoverlabel={"font": {"color": TEXT}},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_xaxes(showgrid=False, zeroline=False, tickfont={"color": TEXT}, title_font={"color": TEXT})
            fig.update_yaxes(
                gridcolor="#243247" if dark else "#E2E8F0",
                zeroline=False,
                tickfont={"color": TEXT},
                title_font={"color": TEXT},
            )
            fig.update_annotations(font_color=TEXT)
            st.plotly_chart(fig, width="stretch")
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
            st.plotly_chart(donut, width="stretch")
            status_date = (
                filtered.dropna(subset=["_confirmed_cum", "_recovered_cum", "_deaths_cum"])
                .sort_values("_tanggal")
                .iloc[-1]["_tanggal"]
                .date()
            )
            st.caption(f"Komposisi kumulatif berdasarkan observasi {status_date:%d %B %Y}. {composition_note}")
    if not period_status.empty:
        with st.container(border=True):
            st.markdown(f"#### Ringkasan per periode · {aggregation}")
            st.caption(
                f"Kasus baru dijumlahkan per periode. Kasus aktif dan total positif kumulatif "
                "adalah snapshot pada observasi terakhir di setiap periode."
            )
            period_status_display = period_status.copy()
            period_status_display["Tanggal"] = pd.to_datetime(period_status_display["Tanggal"]).dt.strftime("%d %b %Y")
            for column in period_status_display.columns[1:]:
                period_status_display[column] = period_status_display[column].map(fmt_num)
            st.dataframe(period_status_display, width="stretch", hide_index=True)
    if fig is not None:
        st.caption(
            f"Periode {aggregation.lower()} dihitung berurutan mulai {start_date:%d %B %Y}. "
            "Kasus baru dijumlahkan; nilai kumulatif menggunakan observasi terakhir pada tiap periode."
        )
    st.subheader("Ringkasan otomatis")
    if not filtered.empty:
        st.write(f"Pada rentang **{start_date:%d %B %Y} sampai {end_date:%d %B %Y}**, dataset memuat {len(filtered)} observasi untuk **Provinsi Jawa Barat**.")
        if not chart_frame.empty:
            peak = chart_frame.loc[chart_frame["Nilai"].idxmax()]
            st.write(f"Nilai tertinggi pada grafik yang dipilih adalah **{fmt_num(peak['Nilai'])}**, pada periode **{pd.to_datetime(peak['Tanggal']).strftime('%d %B %Y')}**.")
        if data_warnings:
            st.info("Catatan data: " + " ".join(data_warnings))
    else:
        st.info("Tidak ada observasi pada rentang waktu yang dipilih.")
with tab_data:
    st.subheader("Data terfilter")
    if filtered.empty:
        st.info("Tidak ada baris untuk filter ini.")
    else:
        display = filtered.copy()
        display["Tanggal"] = display["_tanggal"].dt.strftime("%Y-%m-%d")
        cols = ["Tanggal","_confirmed_daily","_confirmed_cum","_recovered_daily","_recovered_cum","_deaths_daily","_deaths_cum","_active_snapshot"]
        display = display[[c for c in cols if c in display.columns]].rename(columns={
            "_confirmed_daily":"Positif baru", "_confirmed_cum":"Positif kumulatif",
            "_recovered_daily":"Sembuh baru", "_recovered_cum":"Sembuh kumulatif",
            "_deaths_daily":"Meninggal baru", "_deaths_cum":"Meninggal kumulatif", "_active_snapshot":"Kasus aktif (snapshot)"
        })
        st.dataframe(display, width="stretch", hide_index=True)
with tab_sources:
    st.subheader("Sumber data")
    st.markdown(f"- Dataset provinsi: [{SOURCE_URL}]({SOURCE_URL})")
    st.markdown(f"- Dokumentasi repositori: [{SOURCE_REPO}]({SOURCE_REPO})")
    st.write(f"**Sumber yang sedang digunakan:** {source_label}")
    st.write(f"**Cakupan tanggal:** {min_date:%Y-%m-%d} sampai {max_date:%Y-%m-%d}")
    st.write("**Metodologi:** nilai harian yang tersedia langsung dari sumber dipakai sebagaimana adanya. Jika hanya tersedia kumulatif, perubahan harian dihitung sebagai selisih sebelum rentang tampilan diterapkan. Koreksi negatif tidak diubah menjadi nol. Kumulatif dan snapshot aktif tidak dijumlahkan lintas tanggal.")
    st.write("**Cakupan wilayah:** dashboard ini hanya menampilkan data tingkat Provinsi Jawa Barat. Data kabupaten/kota dan kecamatan tidak ditampilkan karena sumber terverifikasi belum tersedia.")
    if source_note:
        st.warning(source_note)
    if data_warnings:
        for warning in data_warnings:
            st.caption(f"Catatan data: {warning}")

download_panel(filtered, chart_frame, source_label, source_url, summary, aggregation, indicator_label, data_warnings)

st.divider()
st.caption("Dashboard edukasi. Periksa sumber, cakupan tanggal, dan definisi indikator sebelum menarik kesimpulan.")
