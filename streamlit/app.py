from __future__ import annotations

import os
import sys
import json
import hashlib
import re
import base64
from html import escape
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from project_config import config_value

DATA = ROOT / "datasets" / "processed"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"
ASSETS = Path(__file__).resolve().parent / "assets"
LOGO = ASSETS / "hospital-intelligence-logo.png"

st.set_page_config(
    page_title="Hospital Operations Intelligence Platform",
    page_icon=str(LOGO),
    layout="wide",
    initial_sidebar_state="auto",
)

COLORS = {
    "teal": "#17A2B8",
    "green": "#28A745",
    "coral": "#DC3545",
    "gold": "#D39E00",
    "blue": "#0F4C81",
    "ink": "#183247",
    "muted": "#627789",
    "line": "#D9E7F0",
    "surface": "#FFFFFF",
    "background": "#F4F9FC",
}
CHART_COLORS = [
    COLORS["teal"],
    COLORS["coral"],
    COLORS["blue"],
    COLORS["gold"],
    COLORS["green"],
    "#75658B",
    "#687880",
    "#A55768",
]

NAVIGATION = [
    "🏠 Home",
    "📈 Executive Dashboard",
    "👥 Patient Intelligence",
    "🩺 Doctor Analytics",
    "🏢 Department Insights",
    "🛏 Bed Management",
    "💰 Revenue Analytics",
    "🤖 AI Prediction Center",
    "📊 Explainable AI",
    "💬 Healthcare Assistant",
    "📄 Reports",
    "⚙ Settings",
]


def current_theme_type() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def inject_css() -> None:
    is_dark = current_theme_type() == "dark"
    theme = {
        "ink": "#EAF3F8" if is_dark else COLORS["ink"],
        "muted": "#AFC1CC" if is_dark else COLORS["muted"],
        "line": "#315064" if is_dark else COLORS["line"],
        "surface": "#122A3A" if is_dark else COLORS["surface"],
        "surface_soft": "#19384A" if is_dark else "#EEF5F5",
        "card": "rgba(18,42,58,.96)" if is_dark else "rgba(255,255,255,.94)",
        "background": "#081823" if is_dark else COLORS["background"],
        "positive": "#76D6AD" if is_dark else "#2B7D63",
        "shadow": "rgba(0,0,0,.28)" if is_dark else "rgba(21,52,59,.06)",
        "color_scheme": "dark" if is_dark else "light",
    }
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700&family=Material+Symbols+Rounded:opsz,wght,FILL@20..48,400,0..1');

        :root {{
            color-scheme: {theme["color_scheme"]};
            --ink: {theme["ink"]};
            --muted: {theme["muted"]};
            --teal: {COLORS["teal"]};
            --green: {COLORS["green"]};
            --coral: {COLORS["coral"]};
            --line: {theme["line"]};
            --surface: {theme["surface"]};
            --surface-soft: {theme["surface_soft"]};
            --card: {theme["card"]};
            --background: {theme["background"]};
            --positive: {theme["positive"]};
            --panel-shadow: {theme["shadow"]};
        }}
        html, body, [class*="css"] {{
            font-family: "Inter", sans-serif;
            color: var(--ink);
            letter-spacing: 0;
        }}
        .stApp {{
            background:
                linear-gradient(180deg, rgba(15,76,129,.045) 0, transparent 260px),
                var(--background);
        }}
        h1, h2, h3 {{
            font-family: "Manrope", sans-serif;
            letter-spacing: 0;
        }}
        [data-testid="stSidebar"] {{
            background: #0B3559;
            border-right: 1px solid rgba(255,255,255,.08);
        }}
        [data-testid="stSidebar"] * {{
            color: #EAF2F2;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{
            min-height: 44px;
            padding: 8px 11px;
            border-radius: 6px;
            transition: background .2s ease, transform .2s ease, box-shadow .2s ease;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{
            display: none;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(255,255,255,.10);
            transform: translateX(3px);
        }}
        [data-testid="stSidebar"] [aria-checked="true"] {{
            background: rgba(23,162,184,.28);
            box-shadow: inset 3px 0 0 #63D4E5;
        }}
        .block-container {{
            max-width: 1480px;
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }}
        .product-header {{
            position: relative;
            overflow: hidden;
            min-height: 142px;
            padding: 24px 28px;
            margin-bottom: 18px;
            color: white;
            background: linear-gradient(112deg, #0B3559 0%, #0F4C81 62%, #117A8B 100%);
            background-size: 180% 180%;
            border: 1px solid rgba(255,255,255,.16);
            border-radius: 8px;
            box-shadow: 0 12px 30px rgba(16,39,44,.16);
            animation: reveal .45s ease-out, headerFlow 10s ease infinite;
        }}
        .product-header::after {{
            content: "";
            position: absolute;
            right: 110px;
            top: 0;
            width: 120px;
            height: 100%;
            border-left: 1px solid rgba(255,255,255,.11);
            border-right: 1px solid rgba(255,255,255,.07);
            transform: skewX(-18deg);
        }}
        .product-eyebrow {{
            margin-bottom: 7px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .product-title {{
            max-width: 900px;
            margin: 0;
            font: 700 31px/1.18 "Manrope", sans-serif;
        }}
        .product-subtitle {{
            max-width: 780px;
            margin: 8px 0 0;
            color: rgba(255,255,255,.82);
            font-size: 14px;
        }}
        .header-status {{
            display: flex;
            flex-wrap: wrap;
            gap: 18px;
            margin-top: 17px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-dot {{
            display: inline-block;
            width: 7px;
            height: 7px;
            margin-right: 6px;
            border-radius: 50%;
            background: #79E6D0;
            box-shadow: 0 0 0 4px rgba(121,230,208,.14);
            animation: pulse 1.8s infinite;
        }}
        .landing-hero {{
            position: relative;
            min-height: min(650px, 72vh);
            display: flex;
            align-items: center;
            overflow: hidden;
            margin: -1.25rem -1rem 22px;
            padding: 48px clamp(28px, 6vw, 84px);
            color: white;
            background-color: #0B3559;
            background-repeat: no-repeat;
            background-position: 92% 50%;
            background-size: min(44vw, 520px);
            background-blend-mode: multiply;
            border-bottom: 5px solid #17A2B8;
            animation: reveal .55s ease-out;
        }}
        .landing-hero::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: rgba(11,53,89,.80);
        }}
        .hero-content {{
            position: relative;
            z-index: 1;
            width: min(780px, 72%);
        }}
        .hero-kicker {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 15px;
            color: #9FE9F2;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .hero-title {{
            margin: 0;
            color: white;
            font: 700 clamp(36px, 5vw, 64px)/1.05 "Manrope", sans-serif;
        }}
        .hero-copy {{
            max-width: 680px;
            margin: 18px 0 20px;
            color: rgba(255,255,255,.82);
            font-size: 17px;
            line-height: 1.65;
        }}
        .hero-capabilities {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px 22px;
            margin-top: 18px;
            font-size: 13px;
            font-weight: 600;
        }}
        .hero-capabilities span::before {{
            content: "check_circle";
            margin-right: 6px;
            color: #79E6D0;
            font-family: "Material Symbols Rounded";
            vertical-align: -3px;
        }}
        .typing-line {{
            min-height: 24px;
            margin-top: 24px;
            color: #9FE9F2;
            font-size: 14px;
            font-weight: 700;
        }}
        .typing-line::after {{
            content: "Predicting readmission risk";
            animation: typingCycle 8s infinite;
        }}
        .experience-band {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 0 0 24px;
        }}
        .experience-item {{
            min-height: 104px;
            padding: 18px;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 7px 20px var(--panel-shadow);
        }}
        .experience-item .material-symbols-rounded {{
            color: var(--teal);
            font-size: 25px;
        }}
        .experience-item strong {{
            display: block;
            margin-top: 10px;
            font-size: 14px;
        }}
        .experience-item small {{
            color: var(--muted);
        }}
        .loading-shell {{
            min-height: 72vh;
            display: grid;
            place-items: center;
            text-align: center;
        }}
        .loading-mark {{
            width: 62px;
            height: 62px;
            margin: 0 auto 18px;
            display: grid;
            place-items: center;
            color: white;
            background: #0F4C81;
            border-radius: 8px;
            box-shadow: 0 0 0 9px rgba(23,162,184,.12);
            animation: loadingPulse 1.25s infinite;
        }}
        .loading-bar {{
            width: min(340px, 72vw);
            height: 6px;
            margin-top: 20px;
            overflow: hidden;
            background: var(--line);
            border-radius: 3px;
        }}
        .loading-bar::after {{
            content: "";
            display: block;
            width: 45%;
            height: 100%;
            background: #17A2B8;
            animation: loadingTravel 1.1s infinite ease-in-out;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(6, minmax(150px, 1fr));
            gap: 12px;
            margin: 4px 0 20px;
        }}
        .kpi-grid.grid-3 {{ grid-template-columns: repeat(3, minmax(140px, 1fr)); }}
        .kpi-grid.grid-4 {{ grid-template-columns: repeat(4, minmax(140px, 1fr)); }}
        .kpi-grid.grid-5 {{ grid-template-columns: repeat(5, minmax(140px, 1fr)); }}
        .kpi-card {{
            position: relative;
            min-height: 112px;
            padding: 16px;
            background: var(--card);
            border: 1px solid var(--line);
            border-top: 3px solid var(--accent);
            border-radius: 8px;
            box-shadow: 0 7px 18px var(--panel-shadow);
            transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-4px) scale(1.01);
            border-color: color-mix(in srgb, var(--accent) 35%, var(--surface));
            box-shadow: 0 14px 28px rgba(15,76,129,.13);
        }}
        .kpi-icon {{
            position: absolute;
            top: 14px;
            right: 14px;
            color: var(--accent);
            font-family: "Material Symbols Rounded";
            font-size: 23px;
        }}
        .kpi-label {{
            color: var(--muted);
            font-size: 12px;
            font-weight: 600;
        }}
        .kpi-value {{
            margin-top: 7px;
            color: var(--ink);
            font: 700 26px/1.1 "Manrope", sans-serif;
        }}
        .kpi-delta {{
            margin-top: 8px;
            color: var(--positive);
            font-size: 11px;
            font-weight: 600;
        }}
        .profile-card, .result-card, .download-card {{
            min-height: 128px;
            padding: 18px;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 8px 22px var(--panel-shadow);
            animation: reveal .35s ease-out;
        }}
        .profile-card strong, .result-card strong {{
            display: block;
            margin-bottom: 8px;
            font: 700 18px/1.25 "Manrope", sans-serif;
        }}
        .profile-meta {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            color: var(--muted);
            font-size: 12px;
        }}
        .result-card {{
            border-left: 5px solid var(--result);
        }}
        .result-label {{
            color: var(--result);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .result-value {{
            margin: 8px 0;
            color: var(--ink);
            font: 700 34px/1 "Manrope", sans-serif;
        }}
        .section-label {{
            margin: 8px 0 12px;
            color: var(--ink);
            font: 700 18px/1.3 "Manrope", sans-serif;
        }}
        .insight-row {{
            padding: 12px 0;
            border-bottom: 1px solid var(--line);
            color: var(--ink);
            font-size: 13px;
        }}
        .risk-high {{ color: #B64532; font-weight: 700; }}
        .risk-medium {{ color: #A87613; font-weight: 700; }}
        .risk-low {{ color: #247B60; font-weight: 700; }}
        .journey {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 8px;
            margin: 10px 0 18px;
        }}
        .journey-step {{
            position: relative;
            padding: 11px 8px;
            text-align: center;
            color: var(--ink);
            background: var(--surface-soft);
            border: 1px solid var(--line);
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}
        .assistant-note {{
            padding: 12px 14px;
            background: var(--surface-soft);
            border-left: 3px solid var(--green);
            border-radius: 0 6px 6px 0;
            color: var(--ink);
            font-size: 12px;
        }}
        .app-footer {{
            margin-top: 30px;
            padding: 24px;
            border-top: 3px solid var(--teal);
            color: #DCEBF5;
            background: #0B3559;
            text-align: center;
            font-size: 12px;
        }}
        div[data-testid="stMetric"] {{
            padding: 13px 14px;
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 8px;
        }}
        div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {{
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 6px 16px var(--panel-shadow);
            overflow: hidden;
            animation: reveal .35s ease-out;
        }}
        .stButton > button, .stDownloadButton > button {{
            min-height: 38px;
            border-radius: 6px;
            font-weight: 600;
            transition: transform .16s ease, box-shadow .16s ease;
        }}
        .stButton > button[kind="primary"] {{
            color: white;
            background: #0F4C81;
            border-color: #0F4C81;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: #0B3E6A;
            border-color: #0B3E6A;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 12px rgba(20,108,110,.12);
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: .65; }}
            50% {{ opacity: 1; }}
        }}
        @keyframes reveal {{
            from {{ opacity: 0; transform: translateY(5px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes headerFlow {{
            0%, 100% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
        }}
        @keyframes typingCycle {{
            0%, 22% {{ content: "Predicting readmission risk"; }}
            25%, 47% {{ content: "Optimizing occupied-bed demand"; }}
            50%, 72% {{ content: "Analyzing claims and revenue"; }}
            75%, 100% {{ content: "Turning evidence into action"; }}
        }}
        @keyframes loadingPulse {{
            0%, 100% {{ transform: scale(.96); opacity: .8; }}
            50% {{ transform: scale(1); opacity: 1; }}
        }}
        @keyframes loadingTravel {{
            from {{ transform: translateX(-110%); }}
            to {{ transform: translateX(245%); }}
        }}
        @media (max-width: 1100px) {{
            .kpi-grid, .kpi-grid.grid-4, .kpi-grid.grid-5 {{
                grid-template-columns: repeat(3, 1fr);
            }}
            .experience-band {{ grid-template-columns: repeat(2, 1fr); }}
            .hero-content {{ width: 82%; }}
        }}
        @media (max-width: 700px) {{
            .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
            .product-header {{ min-height: 165px; padding: 20px; }}
            .product-title {{ font-size: 24px; }}
            .kpi-grid, .kpi-grid.grid-3, .kpi-grid.grid-4,
            .kpi-grid.grid-5 {{ grid-template-columns: repeat(2, 1fr); }}
            .journey {{ grid-template-columns: repeat(2, 1fr); }}
            .landing-hero {{
                min-height: 610px;
                margin-top: 0;
                margin-left: -1rem;
                margin-right: -1rem;
                padding: 32px 22px;
                background-position: 50% 92%;
                background-size: 280px;
            }}
            .landing-hero::before {{ background: rgba(11,53,89,.88); }}
            .hero-content {{ width: 100%; align-self: flex-start; }}
            .hero-title {{ font-size: 38px; }}
            .hero-copy {{ font-size: 15px; }}
            .experience-band {{ grid-template-columns: 1fr 1fr; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def database_url() -> str | None:
    try:
        return st.secrets.get("HOSPITAL_DB_URL") or os.getenv("HOSPITAL_DB_URL")
    except Exception:
        return os.getenv("HOSPITAL_DB_URL")


def requested_data_source() -> str:
    return os.getenv(
        "HOSPITAL_DATA_SOURCE", str(config_value("default_data_source"))
    ).lower()


@st.cache_resource(show_spinner=False)
def database_engine():
    if requested_data_source() != "mysql":
        return None
    url = database_url()
    if not url:
        raise RuntimeError(
            "HOSPITAL_DATA_SOURCE=mysql requires HOSPITAL_DB_URL."
        )
    from sqlalchemy import create_engine, text

    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return engine


@st.cache_data(show_spinner=False)
def load_table(name: str) -> pd.DataFrame:
    if requested_data_source() == "mysql":
        return pd.read_sql_table(name, database_engine())
    candidates = [DATA / f"{name}.csv.gz", DATA / f"{name}.csv"]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    expected = " or ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        f"Required processed table is missing: {expected}. "
        "Run the pipeline locally and commit the compressed deployment tables."
    )


@st.cache_data(show_spinner=False)
def load_report(name: str) -> pd.DataFrame:
    path = REPORTS / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_mart(name: str) -> pd.DataFrame:
    if requested_data_source() == "mysql":
        return pd.read_sql_table(name, database_engine())
    return load_report(f"{name}.csv")


@st.cache_resource(show_spinner=False)
def load_model(name: str):
    path = MODELS / name
    manifest_path = MODELS / "manifest.json"
    if not path.exists() or not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registered = next(
        (
            item
            for item in manifest["artifacts"].values()
            if item["artifact"] == name
        ),
        None,
    )
    if registered is None:
        raise RuntimeError(f"Unregistered model artifact: {name}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != registered["sha256"]:
        raise RuntimeError(f"Model artifact hash mismatch: {name}")
    return joblib.load(path)


@st.cache_data(show_spinner=False)
def load_platform_data() -> dict[str, pd.DataFrame]:
    features = load_table("model_features")
    billing = load_table("billing")
    claims = load_table("claims")
    for frame, columns in [
        (features, ["admit_date", "discharge_date"]),
        (billing, ["claim_billing_date"]),
    ]:
        for column in columns:
            if column in frame:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return {
        "features": features,
        "billing": billing,
        "claims": claims,
        "labs": load_table("labs"),
        "medicines": load_table("medicines"),
        "occupancy": load_report("occupancy_forecast_daily.csv"),
        "insights": load_report("business_insights.csv"),
        "readmission_shap": load_report("readmission_shap_importance.csv"),
        "revenue_shap": load_report("revenue_shap_importance.csv"),
        "patient_explanations": load_report(
            "patient_readmission_explanations.csv"
        ),
        "command_center": load_mart("command_center_kpis"),
        "efficiency_scores": load_mart("hospital_efficiency_scores"),
        "emergency_forecast": load_mart("emergency_forecast"),
        "operational_forecast": load_mart(
            "operational_forecast_summary"
        ),
        "recommendations": load_mart("operational_recommendations"),
    }


def page_header(title: str, subtitle: str, eyebrow: str = "Hospital command center") -> None:
    st.markdown(
        f"""
        <section class="product-header">
            <div class="product-eyebrow">{escape(eyebrow)}</div>
            <h1 class="product-title">{escape(title)}</h1>
            <p class="product-subtitle">{escape(subtitle)}</p>
            <div class="header-status">
                <span><i class="status-dot"></i>Live analytics</span>
                <span><i class="status-dot"></i>ML models online</span>
                <span><i class="status-dot"></i>Operational insights ready</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str) -> None:
    st.markdown(f'<div class="section-label">{escape(title)}</div>', unsafe_allow_html=True)


def asset_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{path.suffix.lstrip('.')};base64,{encoded}"


def metric_icon(label: str) -> str:
    normalized = label.lower()
    icons = {
        "patient": "groups",
        "admission": "medical_services",
        "revenue": "payments",
        "billed": "request_quote",
        "collected": "account_balance_wallet",
        "leakage": "trending_down",
        "readmission": "heart_check",
        "occupancy": "bed",
        "bed": "bed",
        "available": "bedroom_parent",
        "waiting": "schedule",
        "doctor": "stethoscope",
        "department": "domain",
        "quality": "verified",
        "success": "task_alt",
        "payer": "health_and_safety",
        "claim": "description",
        "risk": "monitor_heart",
    }
    return next(
        (icon for term, icon in icons.items() if term in normalized),
        "analytics",
    )


def compact_number(value: float, currency: bool = False) -> str:
    prefix = "$" if currency else ""
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.2f}B"
    if absolute >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"
    if absolute >= 1_000:
        return f"{prefix}{value / 1_000:.1f}K"
    return f"{prefix}{value:,.0f}"


def kpi_grid(items: list[dict[str, str]]) -> None:
    cards = []
    for item in items:
        cards.append(
            f'<div class="kpi-card" style="--accent:{item["color"]}">'
            f'<span class="kpi-icon">{escape(item.get("icon", metric_icon(item["label"])))}</span>'
            f'<div class="kpi-label">{escape(item["label"])}</div>'
            f'<div class="kpi-value">{escape(item["value"])}</div>'
            f'<div class="kpi-delta">{escape(item["delta"])}</div>'
            "</div>"
        )
    grid_class = f" grid-{len(items)}" if 3 <= len(items) <= 5 else ""
    st.markdown(
        f'<div class="kpi-grid{grid_class}">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def result_card(
    label: str,
    value: str,
    detail: str,
    color: str,
) -> None:
    st.markdown(
        f"""
        <div class="result-card" style="--result:{escape(color)}">
            <div class="result-label">{escape(label)}</div>
            <div class="result-value">{escape(value)}</div>
            <div>{escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig, height: int = 350):
    is_dark = current_theme_type() == "dark"
    chart_surface = "#122A3A" if is_dark else "#FFFFFF"
    chart_ink = "#EAF3F8" if is_dark else COLORS["ink"]
    chart_grid = "#29465A" if is_dark else "#EDF1F2"
    hover_surface = "#19384A" if is_dark else "#FFFFFF"
    layout = dict(
        height=height,
        margin=dict(l=18, r=18, t=52, b=18),
        paper_bgcolor=chart_surface,
        plot_bgcolor=chart_surface,
        font=dict(family="Inter", color=chart_ink, size=11),
        legend_title_text="",
        hoverlabel=dict(
            bgcolor=hover_surface,
            bordercolor=chart_grid,
            font=dict(color=chart_ink, size=12),
        ),
    )
    if fig.layout.title.text:
        layout["title_font"] = dict(
            family="Manrope",
            size=15,
            color=chart_ink,
        )
    fig.update_layout(**layout)
    fig.update_xaxes(gridcolor=chart_grid, zeroline=False)
    fig.update_yaxes(gridcolor=chart_grid, zeroline=False)
    return fig


def calculate_historical_occupancy(
    features: pd.DataFrame, capacity: int
) -> pd.DataFrame:
    start = features["admit_date"].dropna().min()
    end = features["admit_date"].dropna().max()
    dates = pd.date_range(start, end, freq="D")
    admissions = features.groupby("admit_date").size()
    discharges = features.groupby(
        features["discharge_date"] + pd.Timedelta(days=1)
    ).size()
    delta = admissions.reindex(dates, fill_value=0) - discharges.reindex(
        dates, fill_value=0
    )
    census = delta.cumsum().clip(lower=0)
    return pd.DataFrame(
        {
            "date": dates,
            "occupied_beds": census.values,
            "occupancy_pct": (census.values / capacity * 100).clip(0, 100),
        }
    )


DOCTOR_NAMES = [
    "Dr. A. Sharma",
    "Dr. R. Patel",
    "Dr. V. Kumar",
    "Dr. N. Singh",
    "Dr. P. Mehta",
    "Dr. S. Iyer",
    "Dr. K. Reddy",
    "Dr. M. Joshi",
    "Dr. T. Rao",
    "Dr. D. Gupta",
]


def doctor_alias(doctor_id: str) -> str:
    digits = "".join(character for character in str(doctor_id) if character.isdigit())
    index = int(digits or 1) - 1
    base = DOCTOR_NAMES[index % len(DOCTOR_NAMES)]
    cycle = index // len(DOCTOR_NAMES) + 1
    return f"{base} · Team {cycle}"


def department_summary(features: pd.DataFrame) -> pd.DataFrame:
    summary = features.groupby("department", as_index=False).agg(
        patients=("patient_id", "nunique"),
        admissions=("admission_id", "count"),
        revenue=("revenue_per_patient", "sum"),
        average_los=("los_days", "mean"),
        average_wait=("waiting_time_minutes", "mean"),
        readmission_rate=("readmitted_30d", "mean"),
        bed_utilization=("bed_utilization_score", "mean"),
    )
    summary["success_rate"] = 1 - summary["readmission_rate"]
    return summary


def doctor_summary(features: pd.DataFrame) -> pd.DataFrame:
    summary = features.groupby(["doctor_id", "department"], as_index=False).agg(
        patients=("patient_id", "nunique"),
        admissions=("admission_id", "count"),
        average_treatment_days=("los_days", "mean"),
        revenue=("revenue_per_patient", "sum"),
        average_wait=("waiting_time_minutes", "mean"),
        readmission_rate=("readmitted_30d", "mean"),
    )
    summary["doctor"] = summary["doctor_id"].map(doctor_alias)
    wait_score = 1 - summary["average_wait"].rank(pct=True)
    outcome_score = 1 - summary["readmission_rate"].rank(pct=True)
    summary["quality_score"] = ((wait_score + outcome_score) / 2 * 100).round(1)
    return summary


def model_input_form(
    features: pd.DataFrame, prefix: str, include_volume: bool = False
) -> tuple[pd.DataFrame, int]:
    numeric_defaults = features.median(numeric_only=True).to_dict()
    row = numeric_defaults.copy()
    for column in features.select_dtypes(exclude="number"):
        mode = features[column].mode()
        row[column] = mode.iloc[0] if not mode.empty else ""

    first, second, third = st.columns(3)
    with first:
        row["age"] = st.number_input(
            "Age", 18, 100, int(row["age"]), key=f"{prefix}_age"
        )
        row["previous_admissions"] = st.number_input(
            "Previous admissions",
            0,
            30,
            int(row["previous_admissions"]),
            key=f"{prefix}_previous",
        )
        row["los_days"] = st.number_input(
            "Length of stay",
            0,
            90,
            int(row["los_days"]),
            key=f"{prefix}_los",
        )
    with second:
        row["charlson_index"] = st.number_input(
            "Charlson comorbidity index",
            0.0,
            15.0,
            float(row["charlson_index"]),
            key=f"{prefix}_charlson",
        )
        row["num_procedures"] = st.number_input(
            "Treatment procedures",
            0,
            20,
            int(row["num_procedures"]),
            key=f"{prefix}_procedures",
        )
        row["medicine_count"] = st.number_input(
            "Medicines",
            0,
            30,
            int(row["medicine_count"]),
            key=f"{prefix}_medicines",
        )
    with third:
        for column, label in [
            ("department", "Department"),
            ("admit_type", "Patient type"),
            ("ward_type", "Ward"),
            ("insurance_category", "Insurance"),
        ]:
            options = sorted(features[column].dropna().astype(str).unique())
            row[column] = st.selectbox(
                label, options, key=f"{prefix}_{column}"
            )

    volume = 1
    if include_volume:
        volume = st.number_input(
            "Expected patient volume", 1, 10000, 250, key=f"{prefix}_volume"
        )

    row["age_group"] = str(
        pd.cut(
            [row["age"]],
            bins=[0, 18, 35, 50, 65, 120],
            labels=["0-18", "19-35", "36-50", "51-65", "66+"],
            include_lowest=True,
        )[0]
    )
    row["lab_abnormality_score"] = (
        int(row["hba1c"] > 7)
        + int(row["creatinine"] > 1.3)
        + int(row["haemoglobin"] < 11)
        + int(row["systolic_bp"] > 140)
    )
    row["disease_severity_score"] = (
        row["charlson_index"] * 2 + row["lab_abnormality_score"]
    )
    row["patient_complexity_index"] = (
        row["disease_severity_score"]
        + row["previous_admissions"]
        + row["num_procedures"]
    )
    row["risk_score"] = (
        0.30 * row["patient_complexity_index"]
        + 0.25 * row["los_days"]
        + 0.20 * row["readmission_history"]
        + 0.15 * row["lab_abnormality_score"]
        + 0.10 * row["department_load"]
    )
    return pd.DataFrame([row]), int(volume)


def model_columns(model) -> list[str]:
    return list(model.named_steps["prep"].feature_names_in_)


def risk_gauge(probability: float, title: str) -> go.Figure:
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability * 100,
            number={"suffix": "%", "font": {"size": 34}},
            title={"text": title, "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": COLORS["coral"]},
                "steps": [
                    {"range": [0, 35], "color": "#DCEFE8"},
                    {"range": [35, 65], "color": "#F5E9C8"},
                    {"range": [65, 100], "color": "#F2D8D2"},
                ],
                "threshold": {
                    "line": {"color": COLORS["ink"], "width": 3},
                    "value": st.session_state.get("risk_threshold", 65),
                },
            },
        )
    )


RISK_FEATURE_LABELS = {
    "los_days": "Length of stay",
    "num_procedures": "Procedure count",
    "charlson_index": "Charlson comorbidity index",
    "hba1c": "HbA1c",
    "creatinine": "Creatinine",
    "haemoglobin": "Haemoglobin",
    "systolic_bp": "Systolic blood pressure",
    "previous_admissions": "Previous admissions",
    "readmission_history": "Readmission history",
    "disease_severity_score": "Disease severity score",
    "lab_abnormality_score": "Abnormal lab indicators",
    "patient_complexity_index": "Patient complexity index",
    "admit_type": "Admission type",
    "ward_type": "Ward type",
    "season": "Admission season",
}


def risk_feature_value(
    source_feature: str,
    category: str | None,
    row: pd.DataFrame,
) -> str:
    if category is not None:
        return category
    value = row.iloc[0][source_feature]
    if source_feature == "los_days":
        return f"{float(value):.0f} days"
    if source_feature == "systolic_bp":
        return f"{float(value):.0f} mmHg"
    if source_feature in {
        "num_procedures",
        "previous_admissions",
        "readmission_history",
        "lab_abnormality_score",
    }:
        return f"{float(value):.0f}"
    return f"{float(value):.2f}"


def local_risk_drivers(
    model,
    row: pd.DataFrame,
    top_n: int = 4,
) -> pd.DataFrame:
    prep = model.named_steps["prep"]
    estimator = model.named_steps["model"]
    transformed = prep.transform(row[model_columns(model)])
    values = (
        transformed.toarray()[0]
        if hasattr(transformed, "toarray")
        else np.asarray(transformed)[0]
    )
    contributions = values * estimator.coef_[0]
    names = prep.get_feature_names_out()
    drivers = pd.DataFrame(
        {
            "transformed_feature": names,
            "contribution": contributions,
        }
    )
    drivers = (
        drivers[drivers["contribution"].abs() > 1e-12]
        .assign(absolute_contribution=lambda frame: frame["contribution"].abs())
        .nlargest(top_n, "absolute_contribution")
    )
    categorical_columns = {
        column
        for column in model_columns(model)
        if not pd.api.types.is_numeric_dtype(row[column])
    }
    metadata = []
    for transformed_name in drivers["transformed_feature"]:
        if transformed_name.startswith("numeric__"):
            source_feature = transformed_name.removeprefix("numeric__")
            category = None
        else:
            encoded = transformed_name.removeprefix("categorical__")
            source_feature = next(
                (
                    column
                    for column in categorical_columns
                    if encoded.startswith(f"{column}_")
                ),
                encoded,
            )
            category = (
                encoded.removeprefix(f"{source_feature}_")
                if source_feature != encoded
                else None
            )
        metadata.append(
            {
                "feature": RISK_FEATURE_LABELS.get(
                    source_feature,
                    source_feature.replace("_", " ").title(),
                ),
                "observed_value": risk_feature_value(
                    source_feature,
                    category,
                    row,
                ),
            }
        )
    drivers = pd.concat(
        [drivers.reset_index(drop=True), pd.DataFrame(metadata)],
        axis=1,
    )
    drivers["direction"] = np.where(
        drivers["contribution"] > 0,
        "Raises model score",
        "Lowers model score",
    )
    drivers["icon"] = np.where(
        drivers["contribution"] > 0,
        "trending_up",
        "trending_down",
    )
    return drivers


def home_page(data: dict[str, pd.DataFrame], capacity: int) -> None:
    logo_uri = asset_data_uri(LOGO)
    st.markdown(
        f"""
        <section class="landing-hero" style="background-image:url('{logo_uri}')">
            <div class="hero-content">
                <div class="hero-kicker">
                    <span class="material-symbols-rounded">health_metrics</span>
                    Hospital operations command center
                </div>
                <h1 class="hero-title">Hospital Operations Intelligence Platform</h1>
                <p class="hero-copy">
                    AI-powered healthcare decision support for safer patient flow,
                    stronger resource planning, and accountable financial performance.
                </p>
                <div class="hero-capabilities">
                    <span>Predictive analytics</span>
                    <span>Machine learning</span>
                    <span>SQL intelligence</span>
                    <span>Executive dashboards</span>
                </div>
                <div class="typing-line"></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "Launch Executive Dashboard",
        type="primary",
        icon=":material/arrow_forward:",
        on_click=lambda: st.session_state.update(
            active_page="📈 Executive Dashboard"
        ),
    )

    required_marts = [
        "command_center",
        "efficiency_scores",
        "operational_forecast",
        "recommendations",
    ]
    if any(data[name].empty for name in required_marts):
        st.error(
            "Operational intelligence marts are unavailable. Run "
            "`python src/operational_intelligence.py`."
        )
        return
    snapshot = data["command_center"].iloc[0]
    hospital_score = data["efficiency_scores"].query(
        "scope_type == 'hospital'"
    ).iloc[0]
    overall_score = float(hospital_score["efficiency_score"])
    department_scores = data["efficiency_scores"].query(
        "scope_type == 'department'"
    )
    score_components = {
        "Patient outcomes": float(hospital_score["patient_outcome_score"]),
        "Collections": float(hospital_score["collection_score"]),
        "Capacity balance": float(
            hospital_score["capacity_balance_score"]
        ),
        "Patient flow": float(hospital_score["patient_flow_score"]),
    }
    forecast = data["operational_forecast"].iloc[0]
    section_title(
        f"Hospital Intelligence Center · latest observed date "
        f"{pd.Timestamp(snapshot['as_of_date']).date()}"
    )
    kpi_grid(
        [
            {
                "label": "Patients today",
                "value": f"{int(snapshot['patients_today']):,}",
                "delta": "Unique patients admitted",
                "color": COLORS["blue"],
            },
            {
                "label": "Bed occupancy",
                "value": f"{float(snapshot['occupancy_pct']):.1f}%",
                "delta": f"{int(snapshot['occupied_beds']):,} occupied beds",
                "color": COLORS["teal"],
            },
            {
                "label": "Emergency wait time",
                "value": f"{float(snapshot['emergency_wait_minutes']):.0f} min",
                "delta": "Simulated queue measure",
                "color": COLORS["gold"],
            },
            {
                "label": "Critical patients",
                "value": f"{int(snapshot['critical_patients']):,}",
                "delta": "ICU or top-complexity cohort",
                "color": COLORS["coral"],
            },
            {
                "label": "Doctor utilization",
                "value": f"{float(snapshot['doctor_utilization_pct']):.0f}%",
                "delta": "Derived workload index",
                "color": COLORS["green"],
            },
            {
                "label": "Efficiency score",
                "value": f"{overall_score:.0f}/100",
                "delta": "Transparent composite index",
                "color": COLORS["blue"],
            },
        ]
    )

    left, right = st.columns([1, 1.45])
    with left:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=overall_score,
                number={"suffix": "/100"},
                title={"text": "Hospital Performance Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": COLORS["blue"]},
                    "steps": [
                        {"range": [0, 60], "color": "#F8D7DA"},
                        {"range": [60, 80], "color": "#FFF2C2"},
                        {"range": [80, 100], "color": "#D8F0E0"},
                    ],
                },
            )
        )
        st.plotly_chart(style_figure(fig, 330), width="stretch")
        component_frame = pd.DataFrame(
            {
                "component": list(score_components),
                "score": list(score_components.values()),
            }
        )
        st.dataframe(
            component_frame,
            width="stretch",
            hide_index=True,
            column_config={
                "score": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.0f",
                )
            },
        )
    with right:
        section_title("Next-week operational outlook")
        kpi_grid(
            [
                {
                    "label": "Emergency patients",
                    "value": f"{int(forecast['emergency_patients']):,}",
                    "delta": (
                        f"{float(forecast['emergency_growth_pct']):+.1f}% "
                        "vs latest week"
                    ),
                    "color": COLORS["coral"],
                },
                {
                    "label": "Additional beds",
                    "value": f"{int(forecast['additional_beds']):+d}",
                    "delta": "Peak occupied-bed requirement",
                    "color": COLORS["teal"],
                },
                {
                    "label": "Peak forecast day",
                    "value": str(forecast["peak_day"]),
                    "delta": f"{int(forecast['peak_day_volume'])} emergency admissions",
                    "color": COLORS["gold"],
                },
            ]
        )
        top_departments = department_scores.nlargest(
            min(8, len(department_scores)),
            "efficiency_score",
        ).sort_values("efficiency_score")
        fig = px.bar(
            top_departments,
            x="efficiency_score",
            y="scope_name",
            orientation="h",
            title="Department efficiency score",
            color="efficiency_score",
            color_continuous_scale=["#FFF2C2", "#6EC5D2", "#0F4C81"],
            range_x=[0, 100],
        )
        st.plotly_chart(style_figure(fig, 390), width="stretch")

    section_title("AI recommendation layer")
    recommendations = data["recommendations"].to_dict("records")
    columns = st.columns(len(recommendations))
    for column, recommendation in zip(columns, recommendations):
        with column:
            st.markdown(
                f"""
                <div class="profile-card">
                    <span class="material-symbols-rounded">clinical_notes</span>
                    <strong>{escape(recommendation["title"])}</strong>
                    <div class="result-label">{escape(recommendation["signal"])}</div>
                    <p>{escape(recommendation["action"])}</p>
                    <small>{escape(recommendation["owner"])} · {escape(recommendation["timeframe"])}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(
        "Forecast uses observed daily emergency admissions and the registered occupied-bed forecast. "
        "Peak-hour prediction is intentionally withheld because source records do not contain arrival timestamps."
    )

    st.markdown(
        """
        <div class="experience-band">
            <div class="experience-item">
                <span class="material-symbols-rounded">monitoring</span>
                <strong>Executive intelligence</strong>
                <small>KPIs, trends, thresholds, and accountable actions</small>
            </div>
            <div class="experience-item">
                <span class="material-symbols-rounded">bed</span>
                <strong>Capacity planning</strong>
                <small>Observed census and occupied-bed forecasts</small>
            </div>
            <div class="experience-item">
                <span class="material-symbols-rounded">monitor_heart</span>
                <strong>Risk decision support</strong>
                <small>Registered models with transparent explanations</small>
            </div>
            <div class="experience-item">
                <span class="material-symbols-rounded">account_balance</span>
                <strong>Financial control</strong>
                <small>Collections, claims, payer mix, and leakage</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def executive_page(data: dict[str, pd.DataFrame], capacity: int) -> None:
    features, billing = data["features"], data["billing"]
    page_header(
        "Executive Operations Dashboard",
        "Monitor patient flow, outcomes, capacity, and financial performance from one command center.",
        "Executive dashboard",
    )
    monthly = (
        features.set_index("admit_date")
        .resample("MS")
        .agg(admissions=("admission_id", "count"), patients=("patient_id", "nunique"))
        .reset_index()
    )
    latest, previous = monthly.iloc[-1], monthly.iloc[-2]
    admission_growth = (latest.admissions / max(previous.admissions, 1) - 1) * 100
    occupancy = calculate_historical_occupancy(features, capacity)
    current_occupancy = occupancy.tail(30)["occupancy_pct"].mean()
    total_revenue = billing["paid_amount"].sum() if not billing.empty else features["revenue_per_patient"].sum()

    kpi_grid(
        [
            {
                "label": "Patients served",
                "value": compact_number(features["patient_id"].nunique()),
                "delta": f"{features['admission_id'].nunique():,} total encounters",
                "color": COLORS["teal"],
            },
            {
                "label": "Latest monthly admissions",
                "value": f"{int(latest.admissions):,}",
                "delta": f"{admission_growth:+.1f}% vs prior month",
                "color": COLORS["blue"],
            },
            {
                "label": "Collected revenue",
                "value": compact_number(total_revenue, currency=True),
                "delta": "Claims and self-pay receipts",
                "color": COLORS["green"],
            },
            {
                "label": "30-day readmission",
                "value": f"{features['readmitted_30d'].mean():.1%}",
                "delta": f"{features['readmitted_30d'].sum():,} flagged admissions",
                "color": COLORS["coral"],
            },
            {
                "label": "Bed occupancy",
                "value": f"{current_occupancy:.1f}%",
                "delta": f"{capacity:,} configured beds",
                "color": COLORS["gold"],
            },
            {
                "label": "Average waiting time",
                "value": f"{features['waiting_time_minutes'].mean():.0f} min",
                "delta": "Simulated workflow measure",
                "color": "#75658B",
            },
        ]
    )

    ward = (
        features.groupby("ward_type", as_index=False)
        .agg(
            admissions=("admission_id", "count"),
            readmission_rate=("readmitted_30d", "mean"),
        )
    )
    monthly_revenue = (
        billing.dropna(subset=["claim_billing_date"])
        .set_index("claim_billing_date")
        .resample("MS")["paid_amount"]
        .sum()
        .reset_index()
    )
    left, right = st.columns([1.35, 1])
    with left:
        fig = px.line(
            monthly,
            x="admit_date",
            y="admissions",
            title="Monthly admissions trend",
            color_discrete_sequence=[COLORS["teal"]],
        )
        fig.update_traces(line_width=2.5, fill="tozeroy", fillcolor="rgba(20,108,110,.08)")
        st.plotly_chart(style_figure(fig), width="stretch")
    with right:
        fig = px.bar(
            ward.sort_values("admissions", ascending=True),
            x="admissions",
            y="ward_type",
            orientation="h",
            color="readmission_rate",
            color_continuous_scale=["#DCEFE8", "#E8B56A", COLORS["coral"]],
            title="Observed ward volume and readmission",
        )
        st.plotly_chart(style_figure(fig), width="stretch")

    left, center, right = st.columns([0.9, 1.3, 0.9])
    with left:
        admission_mix = features.groupby("admit_type", as_index=False).size()
        fig = px.pie(
            admission_mix,
            names="admit_type",
            values="size",
            hole=0.58,
            title="Observed admission-type mix",
            color_discrete_sequence=CHART_COLORS,
        )
        st.plotly_chart(style_figure(fig), width="stretch")
    with center:
        fig = px.area(
            monthly_revenue,
            x="claim_billing_date",
            y="paid_amount",
            title="Collected revenue trend",
            color_discrete_sequence=[COLORS["green"]],
        )
        st.plotly_chart(style_figure(fig), width="stretch")
    with right:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=current_occupancy,
                number={"suffix": "%"},
                title={"text": "30-day bed utilization"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": COLORS["teal"]},
                    "steps": [
                        {"range": [0, 70], "color": "#E8F5EF"},
                        {"range": [70, 85], "color": "#FFF2C2"},
                        {"range": [85, 100], "color": "#F8D7DA"},
                    ],
                    "threshold": {
                        "line": {"color": COLORS["coral"], "width": 3},
                        "value": 85,
                    },
                },
            )
        )
        st.plotly_chart(style_figure(fig), width="stretch")

    left, right = st.columns([1, 1.25])
    with left:
        flow = pd.DataFrame(
            {
                "stage": [
                    "Admissions",
                    "Unique patients",
                    "High-complexity encounters",
                    "30-day readmissions",
                ],
                "volume": [
                    len(features),
                    features["patient_id"].nunique(),
                    int(
                        (
                            features["patient_complexity_index"]
                            >= features["patient_complexity_index"].quantile(0.75)
                        ).sum()
                    ),
                    int(features["readmitted_30d"].sum()),
                ],
            }
        )
        fig = px.funnel(
            flow,
            x="volume",
            y="stage",
            title="Patient flow and risk funnel",
            color_discrete_sequence=[COLORS["blue"]],
        )
        st.plotly_chart(style_figure(fig, 340), width="stretch")
    with right:
        section_title("Operational intelligence")
        if data["insights"].empty:
            st.info("Run the reporting pipeline to generate governed insights.")
        else:
            for insight in data["insights"].itertuples(index=False):
                st.markdown(
                    f'<div class="insight-row"><strong>{escape(str(insight.reliability))}</strong> · '
                    f'{escape(str(insight.insight))}<br><small>{escape(str(insight.decision_use))}</small></div>',
                    unsafe_allow_html=True,
                )


def patient_page(data: dict[str, pd.DataFrame]) -> None:
    features = data["features"]
    page_header(
        "Patient Analytics",
        "Search longitudinal records, segment risk, and follow the patient journey.",
        "Patient intelligence",
    )
    st.warning(
        "Governance: encounter dates, ward, clinical values, LOS, and readmission are observed. "
        "Age, gender, insurance category, department, and doctor are deterministic portfolio derivations."
    )
    search = st.text_input(
        "Find patient",
        placeholder="Enter a complete or partial patient ID",
        help="Searches the processed admissions history.",
    )
    matches = features
    if search:
        matches = features[
            features["patient_id"].astype(str).str.contains(
                search.strip(), case=False, regex=False, na=False
            )
        ]
    patient_ids = matches["patient_id"].drop_duplicates().astype(str).head(1000).tolist()
    if not patient_ids:
        st.warning("No matching patient was found.")
        return
    selected = st.selectbox(
        "Patient record", patient_ids, key="selected_patient_id"
    )
    patient = features[features["patient_id"].astype(str) == selected].sort_values(
        "admit_date"
    )
    latest = patient.iloc[-1]
    risk_class = (
        "HIGH"
        if latest["risk_score"] >= features["risk_score"].quantile(0.75)
        else "MEDIUM"
        if latest["risk_score"] >= features["risk_score"].median()
        else "LOW"
    )
    risk_css = {"HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}[risk_class]
    st.markdown(
        f"""
        <div class="profile-card">
            <strong>Patient {escape(selected)}</strong>
            <div class="profile-meta">
                <span>Latest admission: {escape(str(latest["admit_type"]))}</span>
                <span>Ward: {escape(str(latest["ward_type"]))}</span>
                <span>Department: {escape(str(latest["department"]))}</span>
                <span>Doctor: {escape(doctor_alias(str(latest["doctor_id"])))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    kpi_grid(
        [
            {"label": "Patient age", "value": str(int(latest["age"])), "delta": str(latest["age_group"]), "color": COLORS["blue"]},
            {"label": "Gender", "value": str(latest["gender"]), "delta": "Derived demographic", "color": COLORS["teal"]},
            {"label": "Insurance", "value": str(latest["insurance_category"]), "delta": "Derived category", "color": COLORS["green"]},
            {"label": "Prior admissions", "value": str(int(latest["previous_admissions"])), "delta": "Before latest encounter", "color": COLORS["gold"]},
            {"label": "Complexity index", "value": f"{latest['patient_complexity_index']:.1f}", "delta": "Operational composite", "color": COLORS["teal"]},
            {"label": "Risk group", "value": risk_class, "delta": "Screening classification", "color": {"HIGH": COLORS["coral"], "MEDIUM": COLORS["gold"], "LOW": COLORS["green"]}[risk_class]},
        ]
    )
    st.markdown(
        f'<div class="{risk_css}">Current operational risk classification: {risk_class}</div>',
        unsafe_allow_html=True,
    )

    section_title("Patient journey")
    st.markdown(
        """
        <div class="journey">
            <div class="journey-step">Admission</div>
            <div class="journey-step">Diagnosis</div>
            <div class="journey-step">Treatment</div>
            <div class="journey-step">Lab tests</div>
            <div class="journey-step">Discharge</div>
            <div class="journey-step">Follow-up</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    timeline = patient[
        [
            "admit_date",
            "discharge_date",
            "department",
            "admit_type",
            "los_days",
            "disease_severity_score",
            "readmitted_30d",
        ]
    ].copy()
    timeline["encounter"] = [f"Encounter {i + 1}" for i in range(len(timeline))]
    fig = px.timeline(
        timeline,
        x_start="admit_date",
        x_end="discharge_date",
        y="encounter",
        color="department",
        hover_data=["admit_type", "los_days", "disease_severity_score", "readmitted_30d"],
        title="Admission history",
        color_discrete_sequence=CHART_COLORS,
    )
    st.plotly_chart(style_figure(fig, max(320, 70 + len(timeline) * 40)), width="stretch")

    left, right = st.columns(2)
    with left:
        age_distribution = px.histogram(
            features,
            x="age",
            color="gender",
            nbins=18,
            title="Patient population by age",
            color_discrete_sequence=CHART_COLORS,
        )
        st.plotly_chart(style_figure(age_distribution), width="stretch")
    with right:
        segmentation = (
            features.assign(
                risk_group=pd.qcut(
                    features["risk_score"],
                    3,
                    labels=["Low", "Medium", "High"],
                    duplicates="drop",
                )
            )
            .groupby("risk_group", observed=True)
            .size()
            .reset_index(name="patients")
        )
        fig = px.bar(
            segmentation,
            x="risk_group",
            y="patients",
            color="risk_group",
            title="Operational risk segmentation",
            color_discrete_map={
                "Low": COLORS["green"],
                "Medium": COLORS["gold"],
                "High": COLORS["coral"],
            },
        )
        st.plotly_chart(style_figure(fig), width="stretch")

    section_title("Clinical and operational history")
    st.dataframe(timeline.drop(columns=["encounter"]), width="stretch", hide_index=True)


def doctor_page(data: dict[str, pd.DataFrame]) -> None:
    features = data["features"]
    doctors = doctor_summary(features)
    page_header(
        "Doctor Performance",
        "Balance clinical workload, patient outcomes, throughput, and revenue contribution.",
        "Workforce intelligence",
    )
    st.warning(
        "Demonstration dimension: doctor identities and assignments are derived because the source "
        "contains no provider master data. Use this page to evaluate dashboard workflow, not real staff performance."
    )
    total = len(doctors)
    top = doctors.sort_values("quality_score", ascending=False).iloc[0]
    kpi_grid(
        [
            {
                "label": "Active doctors",
                "value": str(total),
                "delta": "Derived operational roster",
                "color": COLORS["teal"],
            },
            {
                "label": "Patients per doctor",
                "value": f"{doctors['patients'].mean():,.0f}",
                "delta": "Average unique caseload",
                "color": COLORS["blue"],
            },
            {
                "label": "Average treatment time",
                "value": f"{doctors['average_treatment_days'].mean():.1f} days",
                "delta": "Length-of-stay proxy",
                "color": COLORS["gold"],
            },
            {
                "label": "Top quality score",
                "value": f"{top['quality_score']:.0f}/100",
                "delta": str(top["doctor"]),
                "color": COLORS["green"],
            },
            {
                "label": "Average readmission",
                "value": f"{doctors['readmission_rate'].mean():.1%}",
                "delta": "Doctor-level average",
                "color": COLORS["coral"],
            },
            {
                "label": "Revenue per doctor",
                "value": compact_number(doctors["revenue"].mean(), currency=True),
                "delta": "Attributed admissions",
                "color": "#75658B",
            },
        ]
    )
    department_filter = st.multiselect(
        "Department",
        sorted(doctors["department"].unique()),
        default=sorted(doctors["department"].unique()),
    )
    filtered = doctors[doctors["department"].isin(department_filter)]

    section_title("Performance leaders")
    leader_columns = st.columns(3)
    for column, doctor in zip(
        leader_columns,
        filtered.nlargest(3, "quality_score").itertuples(index=False),
    ):
        with column:
            st.markdown(
                f"""
                <div class="profile-card">
                    <strong>{escape(str(doctor.doctor))}</strong>
                    <div class="profile-meta">
                        <span>{escape(str(doctor.department))}</span>
                        <span>Score {doctor.quality_score:.0f}/100</span>
                        <span>{int(doctor.patients):,} patients</span>
                        <span>{doctor.readmission_rate:.1%} readmission</span>
                        <span>{compact_number(doctor.revenue, currency=True)} revenue</span>
                        <span>{doctor.average_treatment_days:.1f} day LOS</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    left, right = st.columns([1.25, 1])
    with left:
        leaderboard = filtered.nlargest(12, "quality_score").sort_values("quality_score")
        fig = px.bar(
            leaderboard,
            x="quality_score",
            y="doctor",
            color="department",
            orientation="h",
            title="Doctor quality leaderboard",
            color_discrete_sequence=CHART_COLORS,
        )
        st.plotly_chart(style_figure(fig, 430), width="stretch")
    with right:
        fig = px.scatter(
            filtered,
            x="admissions",
            y="readmission_rate",
            size="revenue",
            color="department",
            hover_name="doctor",
            title="Workload and patient outcomes",
            color_discrete_sequence=CHART_COLORS,
        )
        st.plotly_chart(style_figure(fig, 430), width="stretch")

    section_title("Performance register")
    st.caption(
        "Doctor names and quality scores are derived presentation aliases because the source contains no names or satisfaction survey."
    )
    display = filtered[
        [
            "doctor",
            "department",
            "patients",
            "admissions",
            "average_treatment_days",
            "revenue",
            "quality_score",
            "readmission_rate",
        ]
    ].sort_values("quality_score", ascending=False)
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "revenue": st.column_config.NumberColumn(format="$%.0f"),
            "readmission_rate": st.column_config.NumberColumn(format="%.1%%"),
            "quality_score": st.column_config.ProgressColumn(min_value=0, max_value=100),
        },
    )


def department_page(data: dict[str, pd.DataFrame]) -> None:
    features = data["features"]
    department = department_summary(features)
    page_header(
        "Department Intelligence",
        "Compare throughput, revenue, capacity pressure, waiting time, and outcomes.",
        "Service-line performance",
    )
    st.warning(
        "Demonstration dimension: department assignments are deterministic derivations. "
        "Observed ward analysis is used for executive conclusions."
    )
    selected = st.selectbox("Focus department", ["All departments", *sorted(department["department"])])
    view = department if selected == "All departments" else department[department["department"] == selected]

    leader = department.loc[department["revenue"].idxmax()]
    busiest = department.loc[department["admissions"].idxmax()]
    kpi_grid(
        [
            {
                "label": "Departments",
                "value": str(len(department)),
                "delta": "Operational service lines",
                "color": COLORS["teal"],
            },
            {
                "label": "Revenue leader",
                "value": str(leader["department"]),
                "delta": compact_number(leader["revenue"], currency=True),
                "color": COLORS["green"],
            },
            {
                "label": "Highest volume",
                "value": str(busiest["department"]),
                "delta": f"{int(busiest['admissions']):,} admissions",
                "color": COLORS["blue"],
            },
            {
                "label": "Average stay",
                "value": f"{view['average_los'].mean():.1f} days",
                "delta": "Selected service lines",
                "color": COLORS["gold"],
            },
            {
                "label": "Success rate",
                "value": f"{view['success_rate'].mean():.1%}",
                "delta": "No 30-day readmission",
                "color": COLORS["green"],
            },
            {
                "label": "Average wait",
                "value": f"{view['average_wait'].mean():.0f} min",
                "delta": "Selected service lines",
                "color": COLORS["coral"],
            },
        ]
    )
    left, right = st.columns([1.2, 1])
    with left:
        fig = px.treemap(
            department,
            path=["department"],
            values="admissions",
            color="revenue",
            hover_data=["average_los", "average_wait", "success_rate"],
            title="Department scale and revenue contribution",
            color_continuous_scale=["#DCEEF8", COLORS["teal"], COLORS["blue"]],
        )
        st.plotly_chart(style_figure(fig, 410), width="stretch")
    with right:
        fig = px.scatter(
            department,
            x="admissions",
            y="average_los",
            size="revenue",
            color="success_rate",
            hover_name="department",
            title="Volume, stay, revenue, and outcomes",
            color_continuous_scale=["#F8D7DA", "#FFF2C2", "#D8F0E0"],
        )
        st.plotly_chart(style_figure(fig, 410), width="stretch")

    matrix = department.set_index("department")[
        ["admissions", "revenue", "average_los", "average_wait", "success_rate"]
    ]
    normalized = (matrix - matrix.min()) / (matrix.max() - matrix.min())
    fig = px.imshow(
        normalized,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale=["#F4F9FC", "#6EC5D2", "#0F4C81"],
        title="Normalized department performance heatmap",
    )
    st.plotly_chart(style_figure(fig, 390), width="stretch")

    ward = features.groupby("ward_type", as_index=False).agg(
        admissions=("admission_id", "count"),
        average_los=("los_days", "mean"),
        readmission_rate=("readmitted_30d", "mean"),
        utilization=("bed_utilization_score", "mean"),
    )
    section_title("Ward and ICU intelligence")
    st.dataframe(
        ward.sort_values("utilization", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "utilization": st.column_config.ProgressColumn(min_value=0, max_value=1),
            "readmission_rate": st.column_config.NumberColumn(format="%.1%%"),
        },
    )


def bed_page(data: dict[str, pd.DataFrame], capacity: int) -> None:
    features = data["features"]
    page_header(
        "Bed Occupancy Analytics",
        "Monitor current census, available capacity, service-line pressure, and future requirements.",
        "Capacity command",
    )
    st.info(
        f"Observed admission/discharge dates drive active census. Occupancy percentages use the "
        f"configured {capacity:,}-bed portfolio assumption, not an authoritative staffed-bed register."
    )
    history = calculate_historical_occupancy(features, capacity)
    current_occupied = int(round(history.tail(7)["occupied_beds"].mean()))
    available = max(capacity - current_occupied, 0)
    occupancy_rate = min(current_occupied / capacity, 1)
    forecast = data["occupancy"].copy()
    if not forecast.empty:
        forecast["forecast_date"] = pd.to_datetime(forecast["forecast_date"])
        forecast["display_occupancy_pct"] = (
            forecast["forecast_occupied_beds"] / capacity * 100
        ).clip(0, 100)

    kpi_grid(
        [
            {
                "label": "Configured beds",
                "value": f"{capacity:,}",
                "delta": "Editable in Settings",
                "color": COLORS["teal"],
            },
            {
                "label": "Occupied",
                "value": f"{current_occupied:,}",
                "delta": "Seven-day average census",
                "color": COLORS["coral"],
            },
            {
                "label": "Available",
                "value": f"{available:,}",
                "delta": "Estimated staffed capacity",
                "color": COLORS["green"],
            },
            {
                "label": "Current utilization",
                "value": f"{occupancy_rate:.1%}",
                "delta": "Across configured capacity",
                "color": COLORS["gold"],
            },
            {
                "label": "30-day requirement",
                "value": f"{int(np.ceil(forecast.head(30)['forecast_occupied_beds'].max())) if not forecast.empty else 0}",
                "delta": "Peak forecast occupied beds",
                "color": COLORS["blue"],
            },
            {
                "label": "Capacity buffer",
                "value": f"{available / capacity:.1%}",
                "delta": "Available share",
                "color": "#75658B",
            },
        ]
    )
    left, right = st.columns([1.35, 1])
    with left:
        recent = history.tail(365)
        fig = px.line(
            recent,
            x="date",
            y="occupancy_pct",
            title="Daily occupancy · trailing 12 months",
            color_discrete_sequence=[COLORS["teal"]],
        )
        fig.add_hline(y=85, line_dash="dash", line_color=COLORS["coral"], annotation_text="85% alert")
        st.plotly_chart(style_figure(fig, 400), width="stretch")
    with right:
        by_department = features.groupby("department", as_index=False)["bed_utilization_score"].mean()
        fig = px.bar(
            by_department.sort_values("bed_utilization_score"),
            x="bed_utilization_score",
            y="department",
            orientation="h",
            title="Relative bed pressure by department",
            color="bed_utilization_score",
            color_continuous_scale=["#DCEFE8", "#E7C06C", COLORS["coral"]],
        )
        st.plotly_chart(style_figure(fig, 400), width="stretch")

    if not forecast.empty:
        horizon = st.segmented_control(
            "Forecast horizon",
            ["Today", "Tomorrow", "7 days", "30 days"],
            default="30 days",
        )
        horizon_days = {
            "Today": 1,
            "Tomorrow": 2,
            "7 days": 7,
            "30 days": 30,
        }
        forecast_view = forecast.head(horizon_days[horizon])
        fig = px.line(
            forecast_view,
            x="forecast_date",
            y="display_occupancy_pct",
            title=f"ML occupancy forecast · {horizon.lower()}",
            color_discrete_sequence=[COLORS["blue"]],
            markers=True,
        )
        fig.update_traces(line_width=2.5)
        st.plotly_chart(style_figure(fig, 360), width="stretch")
        st.caption(
            "Forecast is an operational baseline derived from the provided admissions history and configured capacity."
        )


def revenue_page(data: dict[str, pd.DataFrame]) -> None:
    features, billing = data["features"], data["billing"]
    page_header(
        "Revenue Analytics",
        "Track collections, revenue leakage, payer performance, and service-line contribution.",
        "Financial intelligence",
    )
    st.warning(
        "Payer, billed amount, paid amount, and claim status are observed aggregate evidence. "
        "Admission, department, and doctor revenue attribution uses a surrogate link and is scenario-only."
    )
    paid = billing["paid_amount"].sum()
    billed = billing["billed_amount"].sum()
    gap = billing["claim_gap"].sum()
    approval = (
        data["claims"]["claim_approved"].mean()
        if not data["claims"].empty
        else np.nan
    )
    kpi_grid(
        [
            {
                "label": "Billed revenue",
                "value": compact_number(billed, currency=True),
                "delta": "Submitted charges",
                "color": COLORS["blue"],
            },
            {
                "label": "Collected revenue",
                "value": compact_number(paid, currency=True),
                "delta": f"{paid / max(billed, 1):.1%} realization",
                "color": COLORS["green"],
            },
            {
                "label": "Revenue leakage",
                "value": compact_number(gap, currency=True),
                "delta": "Billed-to-paid gap",
                "color": COLORS["coral"],
            },
            {
                "label": "Claim approval",
                "value": f"{approval:.1%}",
                "delta": "Paid claim lines",
                "color": COLORS["teal"],
            },
            {
                "label": "Revenue per admission",
                "value": compact_number(features["revenue_per_patient"].mean(), currency=True),
                "delta": "Modeled admission value",
                "color": COLORS["gold"],
            },
            {
                "label": "Payers",
                "value": str(load_table("insurance")["insurance_provider"].nunique()),
                "delta": "Insurance providers",
                "color": "#75658B",
            },
        ]
    )
    monthly = (
        billing.dropna(subset=["claim_billing_date"])
        .set_index("claim_billing_date")
        .resample("MS")
        .agg(billed=("billed_amount", "sum"), paid=("paid_amount", "sum"))
        .reset_index()
    )
    insurance = (
        billing.merge(
            load_table("insurance"),
            on="insurance_id",
            how="left",
            validate="many_to_one",
        )
        .merge(
            data["claims"][["billing_id", "claim_approved"]],
            on="billing_id",
            how="left",
            validate="one_to_one",
        )
    )
    department = department_summary(features)
    doctors = doctor_summary(features)
    left, right = st.columns([1.35, 1])
    with left:
        long_monthly = monthly.melt(
            id_vars="claim_billing_date",
            value_vars=["billed", "paid"],
            var_name="measure",
            value_name="amount",
        )
        fig = px.line(
            long_monthly,
            x="claim_billing_date",
            y="amount",
            color="measure",
            title="Billed and collected revenue",
            color_discrete_map={"billed": COLORS["blue"], "paid": COLORS["green"]},
        )
        st.plotly_chart(style_figure(fig, 390), width="stretch")
    with right:
        fig = px.bar(
            department.sort_values("revenue"),
            x="revenue",
            y="department",
            orientation="h",
            title="Department revenue contribution",
            color="revenue",
            color_continuous_scale=["#DCEFE8", COLORS["teal"]],
        )
        st.plotly_chart(style_figure(fig, 390), width="stretch")

    left, right = st.columns(2)
    with left:
        if not insurance.empty and "insurance_provider" in insurance:
            payer = insurance.groupby("insurance_provider", as_index=False).agg(
                billed=("billed_amount", "sum"),
                paid=("paid_amount", "sum"),
                approval=("claim_approved", "mean"),
            )
            fig = px.scatter(
                payer,
                x="billed",
                y="paid",
                size="approval",
                color="insurance_provider",
                title="Insurance performance",
                color_discrete_sequence=CHART_COLORS,
            )
            st.plotly_chart(style_figure(fig), width="stretch")
    with right:
        fig = px.bar(
            doctors.nlargest(12, "revenue").sort_values("revenue"),
            x="revenue",
            y="doctor",
            orientation="h",
            color="department",
            title="Doctor-attributed revenue",
            color_discrete_sequence=CHART_COLORS,
        )
        st.plotly_chart(style_figure(fig), width="stretch")

    top_department = department.loc[department["revenue"].idxmax()]
    contribution = top_department["revenue"] / department["revenue"].sum()
    st.markdown(
        f"""
        <div class="assistant-note">
            <strong>AI insight:</strong> {escape(str(top_department["department"]))}
            contributes {contribution:.1%} of modeled department revenue. Review its
            payer mix and capacity before reallocating resources.
        </div>
        """,
        unsafe_allow_html=True,
    )


def predictions_page(data: dict[str, pd.DataFrame]) -> None:
    features = data["features"]
    page_header(
        "AI Prediction Center",
        "Run patient-level risk, waiting-time, and financial scenarios through trained pipelines.",
        "Decision support models",
    )
    readmission_model = load_model("readmission.pkl")
    waiting_model = load_model("waiting.pkl")
    revenue_model = load_model("revenue.pkl")
    tab_readmission, tab_wait, tab_revenue = st.tabs(
        ["Readmission risk", "Waiting simulation", "Revenue scenario"]
    )
    with tab_readmission:
        if readmission_model is None:
            st.error("Readmission model artifact is unavailable.")
        else:
            input_mode = st.segmented_control(
                "Prediction input",
                ["Patient record", "Custom scenario"],
                default="Patient record",
            )
            row = None
            selected_patient = None
            if input_mode == "Patient record":
                patient_query = st.text_input(
                    "Patient ID",
                    value=str(st.session_state.get("selected_patient_id", "")),
                    placeholder="Enter a complete or partial patient ID",
                )
                patient_matches = features
                if patient_query.strip():
                    patient_matches = features[
                        features["patient_id"].astype(str).str.contains(
                            patient_query.strip(),
                            case=False,
                            regex=False,
                            na=False,
                        )
                    ]
                patient_ids = (
                    patient_matches["patient_id"]
                    .drop_duplicates()
                    .astype(str)
                    .head(200)
                    .tolist()
                )
                if patient_ids:
                    selected_patient = st.selectbox(
                        "Matching patient record",
                        patient_ids,
                        key="prediction_patient_id",
                    )
                    row = (
                        features[
                            features["patient_id"].astype(str)
                            == selected_patient
                        ]
                        .sort_values("admit_date")
                        .tail(1)
                    )
                    latest = row.iloc[0]
                    st.markdown(
                        f"""
                        <div class="profile-card">
                            <strong>Patient {escape(selected_patient)}</strong>
                            <div class="profile-meta">
                                <span>{escape(str(latest["ward_type"]))} ward</span>
                                <span>{escape(str(latest["admit_type"]))} admission</span>
                                <span>{int(latest["previous_admissions"])} previous admissions</span>
                                <span>{int(latest["lab_abnormality_score"])} abnormal lab indicators</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("No matching patient record was found.")
            else:
                with st.form("readmission_prediction_inputs"):
                    row, _ = model_input_form(features, "readmission")
                    st.form_submit_button(
                        "Apply custom inputs",
                        type="secondary",
                    )

            submit = False
            if row is not None:
                with st.form("readmission_prediction"):
                    submit = st.form_submit_button(
                        "Analyze readmission risk",
                        type="primary",
                    )
            if submit:
                probability = float(
                    readmission_model.predict_proba(
                        row[model_columns(readmission_model)]
                    )[0, 1]
                )
                threshold = st.session_state.get("risk_threshold", 65) / 100
                label = "HIGH RISK" if probability >= threshold else "MONITOR" if probability >= 0.35 else "LOW RISK"
                left, right = st.columns([1, 1.5])
                with left:
                    fig = risk_gauge(probability, "30-day probability")
                    st.plotly_chart(style_figure(fig, 310), width="stretch")
                with right:
                    risk_color = (
                        COLORS["coral"]
                        if label == "HIGH RISK"
                        else COLORS["gold"]
                        if label == "MONITOR"
                        else COLORS["green"]
                    )
                    recommendation = (
                        "Prioritize discharge review and schedule follow-up."
                        if label == "HIGH RISK"
                        else "Review risk factors and monitor after discharge."
                        if label == "MONITOR"
                        else "Continue standard follow-up protocol."
                    )
                    result_card(
                        "Readmission classification",
                        label,
                        f"{probability:.1%} estimated probability",
                        risk_color,
                    )
                    st.success(recommendation)
                    st.info(
                        "Use this score to prioritize review and discharge follow-up. It does not replace clinical judgment."
                    )
                drivers = local_risk_drivers(readmission_model, row)
                section_title("Why this risk level?")
                if drivers.empty:
                    st.info(
                        "No non-zero model contributions were identified for this scenario."
                    )
                else:
                    driver_columns = st.columns(len(drivers))
                    for column, driver in zip(
                        driver_columns,
                        drivers.itertuples(index=False),
                    ):
                        with column:
                            st.markdown(
                                f"""
                                <div class="experience-item">
                                    <span class="material-symbols-rounded">{escape(str(driver.icon))}</span>
                                    <strong>{escape(str(driver.feature))}</strong>
                                    <small>Patient value: {escape(str(driver.observed_value))}</small><br>
                                    <small>{escape(str(driver.direction))}: {driver.contribution:+.3f} log-odds</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                st.caption(
                    "Cards show the four largest absolute contributions from the registered "
                    "logistic-regression pipeline. Up raises and down lowers the model score; "
                    "the probability also includes every other feature and the learned intercept. "
                    "These values explain model behavior and are not clinical diagnoses."
                )
    with tab_wait:
        if waiting_model is None:
            st.error("Waiting-time model artifact is unavailable.")
        else:
            with st.form("waiting_prediction"):
                row, _ = model_input_form(features, "waiting")
                submit = st.form_submit_button(
                    "Estimate waiting time",
                    type="primary",
                )
            if submit:
                prediction = max(
                    0.0,
                    float(waiting_model.predict(row[model_columns(waiting_model)])[0]),
                )
                result_card(
                    "Waiting-time scenario",
                    f"{prediction:.0f} minutes",
                    "Estimated service delay for the selected operational scenario",
                    COLORS["gold"],
                )
                st.warning(
                    "The source has no observed queue timestamps. This is a workflow simulation, not an operational forecast."
                )
                department_average = features.loc[
                    features["department"] == row.iloc[0]["department"],
                    "waiting_time_minutes",
                ].mean()
                st.caption(
                    f"Department baseline: {department_average:.0f} minutes. Scenario difference: {prediction - department_average:+.0f} minutes."
                )
    with tab_revenue:
        if revenue_model is None:
            st.error("Revenue model artifact is unavailable.")
        else:
            with st.form("revenue_prediction"):
                row, volume = model_input_form(features, "revenue", include_volume=True)
                submit = st.form_submit_button(
                    "Forecast revenue scenario",
                    type="primary",
                )
            if submit:
                per_admission = max(
                    0.0,
                    float(revenue_model.predict(row[model_columns(revenue_model)])[0]),
                )
                total = per_admission * volume
                kpi_grid(
                    [
                        {
                            "label": "Revenue per admission",
                            "value": f"${per_admission:,.0f}",
                            "delta": "Modeled scenario value",
                            "color": COLORS["teal"],
                        },
                        {
                            "label": "Patient volume",
                            "value": f"{volume:,}",
                            "delta": "Selected planning volume",
                            "color": COLORS["blue"],
                        },
                        {
                            "label": "Expected revenue",
                            "value": f"${total:,.0f}",
                            "delta": "Scenario total",
                            "color": COLORS["green"],
                        },
                    ]
                )
                st.warning(
                    "Admission-level revenue uses a surrogate claims link and simulated values where no linked claim exists. Treat this as a planning scenario."
                )


def explainability_page(data: dict[str, pd.DataFrame]) -> None:
    page_header(
        "Explainable AI",
        "Understand which clinical and operational variables influence model behavior.",
        "Model transparency",
    )
    model_name = st.segmented_control(
        "Model explanation",
        ["Readmission", "Revenue"],
        default="Readmission",
    )
    shap_data = (
        data["readmission_shap"]
        if model_name == "Readmission"
        else data["revenue_shap"]
    )
    if shap_data.empty:
        st.warning("Run the SHAP pipeline to generate explainability reports.")
        return
    top = shap_data.nlargest(18, "mean_abs_shap").sort_values("mean_abs_shap")
    top["feature"] = (
        top["feature"]
        .str.replace("num__", "", regex=False)
        .str.replace("cat__", "", regex=False)
        .str.replace("_", " ")
        .str.title()
    )
    left, right = st.columns([1.4, 1])
    with left:
        fig = px.bar(
            top,
            x="mean_abs_shap",
            y="feature",
            orientation="h",
            title=f"{model_name} feature impact",
            color="mean_abs_shap",
            color_continuous_scale=["#DCEFE8", COLORS["teal"]],
        )
        st.plotly_chart(style_figure(fig, 560), width="stretch")
    with right:
        section_title("How to read this")
        st.markdown(
            """
            <div class="assistant-note">
                SHAP impact measures how strongly each variable changes model output.
                Larger bars matter more globally. Direction and clinical meaning must
                be reviewed for the individual patient before action.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric("Features explained", f"{len(shap_data):,}")
        st.metric("Leading driver", top.iloc[-1]["feature"])
        st.metric("Model scope", f"{model_name} prediction")
        st.caption(
            "Patient-level readmission explanations are generated for the audited SHAP sample."
        )
    if model_name == "Readmission" and not data["patient_explanations"].empty:
        section_title("Patient-level risk explanations")
        explanations = data["patient_explanations"].copy()
        explanations["top_risk_factor"] = (
            explanations["top_risk_factor"]
            .str.replace("num__", "", regex=False)
            .str.replace("cat__", "", regex=False)
            .str.replace("_", " ")
            .str.title()
        )
        st.dataframe(explanations.head(100), width="stretch", hide_index=True)


def resolve_patient_id(
    question: str,
    features: pd.DataFrame,
    patient_context: str | None = None,
) -> tuple[str | None, bool]:
    patient_ids = features["patient_id"].dropna().astype(str).drop_duplicates()
    lookup = {patient_id.lower(): patient_id for patient_id in patient_ids}
    context = str(patient_context or "").strip()
    if context:
        exact = lookup.get(context.lower())
        if exact:
            return exact, True
        partial = patient_ids[
            patient_ids.str.contains(context, case=False, regex=False)
        ]
        if len(partial) == 1:
            return str(partial.iloc[0]), True
        return None, False

    for token in re.findall(r"[a-zA-Z0-9-]{6,}", question):
        exact = lookup.get(token.lower())
        if exact:
            return exact, True
        partial = patient_ids[
            patient_ids.str.contains(token, case=False, regex=False)
        ]
        if len(partial) == 1:
            return str(partial.iloc[0]), True
    return None, True


def patient_record_answer(
    patient_id: str,
    features: pd.DataFrame,
    duration_question: bool,
) -> str:
    history = features[
        features["patient_id"].astype(str) == patient_id
    ].sort_values("admit_date")
    latest = history.iloc[-1]
    ward_average = features.groupby("ward_type")["los_days"].mean().get(
        latest["ward_type"], np.nan
    )
    admit_date = pd.Timestamp(latest["admit_date"]).date()
    discharge_date = pd.Timestamp(latest["discharge_date"]).date()

    if duration_question:
        return (
            f"I cannot predict when patient {patient_id} will be cured. The latest "
            f"record shows an observed stay of {latest['los_days']:.0f} days "
            f"({admit_date} to {discharge_date}); the historical average for "
            f"{latest['ward_type']} is {ward_average:.1f} days. Length of stay is "
            "not a recovery prognosis. A treating clinician must estimate recovery "
            "using the diagnosis, treatment response, and current examination."
        )

    abnormal_labs = int(latest["lab_abnormality_score"])
    readmission_label = (
        "was readmitted within 30 days"
        if int(latest["readmitted_30d"]) == 1
        else "was not recorded as readmitted within 30 days"
    )
    return (
        f"Patient {patient_id}'s latest recorded encounter was a "
        f"{latest['admit_type']} admission in {latest['ward_type']} from "
        f"{admit_date} to {discharge_date}. The record shows Charlson index "
        f"{latest['charlson_index']:.0f}, derived severity score "
        f"{latest['disease_severity_score']:.0f}, and {abnormal_labs} abnormal "
        f"lab indicator(s); the patient {readmission_label}. This summarizes the "
        "available historical record and is not a diagnosis or current-condition assessment."
    )


def assistant_answer(
    question: str,
    data: dict[str, pd.DataFrame],
    capacity: int,
    patient_context: str | None = None,
) -> str:
    features, billing = data["features"], data["billing"]
    normalized = question.lower().strip()
    patient_status_terms = [
        "condition",
        "patient status",
        "how is the patient",
        "health of",
        "diagnosis",
    ]
    duration_terms = [
        "cure",
        "recover",
        "recovery",
        "how long",
        "treatment time",
        "discharge time",
    ]
    is_patient_status = any(term in normalized for term in patient_status_terms)
    is_duration = any(term in normalized for term in duration_terms)
    if is_patient_status or is_duration:
        patient_id, context_valid = resolve_patient_id(
            question, features, patient_context
        )
        if not context_valid:
            return (
                "I could not find that patient ID. Enter a complete patient ID, "
                "or a unique part of it, in Patient ID context."
            )
        if patient_id:
            return patient_record_answer(patient_id, features, is_duration)
        if is_duration:
            return (
                "I cannot estimate a cure or recovery time from hospital operations "
                "data. Enter a patient ID if you want the recorded length of stay and "
                "the ward's historical average; those values are not a medical prognosis."
            )
        return (
            "Please provide a patient ID or select a patient on Patient Analytics. "
            "I can summarize the latest recorded encounter, severity indicators, "
            "length of stay, and readmission status, but I cannot diagnose a current condition."
        )
    if "icu" in normalized or "occupancy" in normalized or "bed" in normalized:
        icu = features[features["ward_type"].astype(str).str.upper() == "ICU"]
        weekend = icu["is_weekend_admission"].mean() if not icu.empty else 0
        history = calculate_historical_occupancy(features, capacity)
        current = history.tail(30)["occupancy_pct"].mean()
        return (
            f"Current 30-day occupancy is approximately {current:.1f}% of the "
            f"{capacity:,}-bed configured capacity. ICU records account for "
            f"{len(icu):,} admissions, and {weekend:.1%} arrive on weekends. "
            "Review weekend emergency inflow and discharge timing before changing staffing."
        )
    if "readmission" in normalized or "risk" in normalized:
        ward = (
            features.groupby("ward_type", as_index=False)
            .agg(readmission_rate=("readmitted_30d", "mean"))
        )
        highest = ward.loc[ward["readmission_rate"].idxmax()]
        return (
            f"{highest['ward_type']} has the highest observed 30-day readmission "
            f"rate at {highest['readmission_rate']:.1%}. SHAP identifies length of "
            "stay, Charlson index, haemoglobin, severity, and patient complexity as "
            "the leading global risk drivers."
        )
    if "revenue" in normalized or "claim" in normalized or "finance" in normalized:
        department = department_summary(features)
        top = department.loc[department["revenue"].idxmax()]
        gap = billing["claim_gap"].sum()
        return (
            f"{top['department']} is the largest modeled revenue contributor. "
            f"The billed-to-paid gap is ${gap:,.0f}. Prioritize denied-claim review "
            "and payer-specific leakage analysis before interpreting revenue growth."
        )
    if "wait" in normalized or "queue" in normalized:
        wait = features.groupby("department")["waiting_time_minutes"].mean()
        return (
            f"{wait.idxmax()} currently has the longest modeled average wait at "
            f"{wait.max():.0f} minutes, compared with {features['waiting_time_minutes'].mean():.0f} "
            "minutes hospital-wide. Examine arrival mix, doctor coverage, and weekend load."
        )
    if "doctor" in normalized or "workload" in normalized:
        doctors = doctor_summary(features)
        busiest = doctors.loc[doctors["admissions"].idxmax()]
        return (
            f"{busiest['doctor']} has the largest derived workload at "
            f"{int(busiest['admissions']):,} admissions. Compare this with "
            f"{busiest['readmission_rate']:.1%} readmission and "
            f"{busiest['average_wait']:.0f}-minute average waiting time before rebalancing."
        )
    return (
        "I can analyze occupancy, ICU pressure, readmissions, waiting time, doctor "
        "workload, revenue, and claims. Ask a focused operational question for a "
        "data-grounded response."
    )


def assistant_panel(data: dict[str, pd.DataFrame], capacity: int) -> None:
    section_title("AI hospital operations assistant")
    st.markdown(
        '<div class="assistant-note">Ask about occupancy, readmissions, waiting time, doctor workload, revenue, claims, or a patient record. This assistant summarizes loaded analytics; it does not diagnose illness or predict recovery.</div>',
        unsafe_allow_html=True,
    )
    patient_context = st.text_input(
        "Patient ID context",
        value=str(st.session_state.get("selected_patient_id", "")),
        placeholder="Optional: complete or unique partial patient ID",
        key="assistant_patient_context",
    )
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = [
            {
                "role": "assistant",
                "content": "Hospital analytics are loaded. What operational question should we investigate?",
            }
        ]
    for message in st.session_state.assistant_messages[-8:]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    prompt = st.chat_input("Ask an operational question")
    if prompt:
        st.session_state.assistant_messages.append({"role": "user", "content": prompt})
        answer = assistant_answer(prompt, data, capacity, patient_context)
        st.session_state.assistant_messages.append(
            {"role": "assistant", "content": answer}
        )
        st.rerun()


def assistant_page(data: dict[str, pd.DataFrame], capacity: int) -> None:
    page_header(
        "Healthcare Operations Assistant",
        "Investigate hospital performance using answers grounded in the loaded analytics tables.",
        "Conversational intelligence",
    )
    prompts = st.columns(4)
    examples = [
        ("Bed pressure", "Show ICU occupancy and weekend pressure."),
        ("Readmissions", "Which ward has the highest readmission rate?"),
        ("Revenue", "Where is claims revenue leaking?"),
        ("Workload", "Which doctor has the largest derived workload?"),
    ]
    for column, (title, prompt) in zip(prompts, examples):
        with column:
            st.markdown(
                f"""
                <div class="experience-item">
                    <span class="material-symbols-rounded">forum</span>
                    <strong>{escape(title)}</strong>
                    <small>{escape(prompt)}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
    assistant_panel(data, capacity)


def reports_page(data: dict[str, pd.DataFrame], capacity: int) -> None:
    page_header(
        "Report Center",
        "Generate executive reporting and download governed analytical outputs.",
        "Decision distribution",
    )
    left, right = st.columns([1, 1.4])
    with left:
        section_title("Executive report")
        st.markdown(
            """
            <div class="download-card">
                <span class="material-symbols-rounded">picture_as_pdf</span>
                <strong>Executive decision pack</strong><br>
                <small>KPIs, trends, thresholds, owners, and management actions</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        pdf_path = REPORTS / "executive_report.pdf"
        if st.button("Refresh executive PDF", type="primary", width="stretch"):
            with st.spinner("Analyzing hospital data and building the report..."):
                from generate_executive_report import main as generate_report
                from operational_intelligence import main as generate_marts

                generate_marts()
                generate_report()
                load_report.clear()
                load_mart.clear()
                load_platform_data.clear()
            st.success("Executive report refreshed.")
        if pdf_path.exists():
            st.download_button(
                "Download executive PDF",
                pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
                width="stretch",
            )
        st.caption("Includes executive KPIs, management insights, and department charts.")
    with right:
        section_title("Available analytical outputs")
        files = (
            sorted(REPORTS.glob("*.csv"))
            + sorted(REPORTS.glob("*.json"))
            + sorted((ROOT / "excel").glob("*.xlsx"))
        )
        file_table = pd.DataFrame(
            [
                {
                    "report": file.name,
                    "type": file.suffix.upper().lstrip("."),
                    "size_kb": round(file.stat().st_size / 1024, 1),
                    "updated": pd.Timestamp(file.stat().st_mtime, unit="s"),
                }
                for file in files
            ]
        )
        st.dataframe(file_table, width="stretch", hide_index=True)
        selected = st.selectbox("Download data report", [file.name for file in files])
        selected_path = next(file for file in files if file.name == selected)
        st.download_button(
            "Download selected report",
            selected_path.read_bytes(),
            file_name=selected_path.name,
            width="stretch",
        )


def settings_page(data: dict[str, pd.DataFrame]) -> None:
    page_header(
        "Platform Settings",
        "Configure operational assumptions, model thresholds, data source, and cache behavior.",
        "Administration",
    )
    first, second = st.columns(2)
    with first:
        section_title("Operational assumptions")
        st.session_state.bed_capacity = st.number_input(
            "Configured staffed beds",
            min_value=50,
            max_value=5000,
            value=int(
                st.session_state.get(
                    "bed_capacity", int(config_value("bed_capacity"))
                )
            ),
            step=10,
        )
        st.session_state.risk_threshold = st.slider(
            "High-risk threshold",
            min_value=40,
            max_value=90,
            value=int(
                st.session_state.get(
                    "risk_threshold",
                    round(float(config_value("high_risk_threshold")) * 100),
                )
            ),
            format="%d%%",
        )
        st.selectbox("Display currency", ["USD"], disabled=True)
    with second:
        section_title("Data connection")
        source = (
            "MySQL warehouse"
            if requested_data_source() == "mysql"
            else "Processed CSV"
        )
        st.metric("Active source", source)
        st.metric("Admissions loaded", f"{len(data['features']):,}")
        st.metric("Billing rows loaded", f"{len(data['billing']):,}")
        st.code(
            "Set HOSPITAL_DB_URL=mysql+mysqlconnector://user:password@host/hospital_ops",
            language="text",
        )
        mysql_status_path = REPORTS / "mysql_deployment_status.json"
        if mysql_status_path.exists():
            mysql_status = json.loads(
                mysql_status_path.read_text(encoding="utf-8")
            )
            status_label = str(mysql_status.get("status", "unknown")).replace(
                "_", " "
            ).title()
            st.metric("MySQL deployment evidence", status_label)
            if mysql_status.get("status") == "verified":
                st.success(
                    f"MySQL {mysql_status.get('mysql_version', '')} verified with "
                    f"{mysql_status.get('tables_verified', 0)} tables and "
                    f"{mysql_status.get('views_verified', 0)} views."
                )
            else:
                st.caption(
                    str(
                        mysql_status.get(
                            "reason",
                            "Run the MySQL verifier to generate deployment evidence.",
                        )
                    )
                )
        if st.button("Clear application cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared. Reload the page to refresh all resources.")
    section_title("Governance")
    st.warning(
        "This portfolio system contains derived demographics, doctor aliases, department assignments, surrogate claim links, and capacity assumptions. Validate against governed hospital systems before operational or clinical use."
    )


def footer() -> None:
    st.markdown(
        """
        <footer class="app-footer">
            <strong>Hospital Operations Intelligence Platform</strong><br>
            Python &nbsp;|&nbsp; MySQL &nbsp;|&nbsp; Machine Learning &nbsp;|&nbsp; Power BI &nbsp;|&nbsp; Streamlit<br><br>
            Developed by Suhani Chauhan &nbsp;|&nbsp; Governed analytics with transparent operational assumptions
        </footer>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()
    if "bed_capacity" not in st.session_state:
        st.session_state.bed_capacity = int(config_value("bed_capacity"))
    if "risk_threshold" not in st.session_state:
        st.session_state.risk_threshold = round(
            float(config_value("high_risk_threshold")) * 100
        )

    loading_slot = st.empty()
    if not st.session_state.get("platform_loaded"):
        loading_slot.markdown(
            """
            <div class="loading-shell">
                <div>
                    <div class="loading-mark">
                        <span class="material-symbols-rounded">health_metrics</span>
                    </div>
                    <h2>Loading Hospital Analytics</h2>
                    <p>Preparing governed KPIs, forecasts, and model artifacts...</p>
                    <div class="loading-bar"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with st.spinner("Loading hospital intelligence...", show_time=True):
        data = load_platform_data()
    st.session_state.platform_loaded = True
    loading_slot.empty()
    if data["features"].empty:
        st.error("Processed hospital data is unavailable. Run `python src/data_pipeline.py`.")
        st.stop()

    with st.sidebar:
        st.image(str(LOGO), width=82)
        st.markdown("### Hospital AI")
        st.caption("Operations command center")
        page = st.radio(
            "Navigation",
            NAVIGATION,
            label_visibility="collapsed",
            key="active_page",
        )
        st.divider()
        st.caption(
            f"Source: {requested_data_source().upper()} · "
            f"{len(data['features']):,} admissions"
        )

    capacity = int(st.session_state.bed_capacity)
    routes = {
        "🏠 Home": lambda: home_page(data, capacity),
        "📈 Executive Dashboard": lambda: executive_page(data, capacity),
        "👥 Patient Intelligence": lambda: patient_page(data),
        "🩺 Doctor Analytics": lambda: doctor_page(data),
        "🏢 Department Insights": lambda: department_page(data),
        "🛏 Bed Management": lambda: bed_page(data, capacity),
        "💰 Revenue Analytics": lambda: revenue_page(data),
        "🤖 AI Prediction Center": lambda: predictions_page(data),
        "📊 Explainable AI": lambda: explainability_page(data),
        "💬 Healthcare Assistant": lambda: assistant_page(data, capacity),
        "📄 Reports": lambda: reports_page(data, capacity),
        "⚙ Settings": lambda: settings_page(data),
    }
    routes[page]()
    footer()


if __name__ == "__main__":
    main()
