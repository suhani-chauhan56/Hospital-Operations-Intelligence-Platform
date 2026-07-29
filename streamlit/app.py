from __future__ import annotations

import os
import sys
import json
import hashlib
import re
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
    "teal": "#146C6E",
    "green": "#269A78",
    "coral": "#D7644A",
    "gold": "#C9962B",
    "blue": "#3D6E8F",
    "ink": "#17242B",
    "muted": "#64747C",
    "line": "#DCE5E7",
    "surface": "#FFFFFF",
    "background": "#F4F7F8",
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


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700&display=swap');

        :root {{
            --ink: {COLORS["ink"]};
            --muted: {COLORS["muted"]};
            --teal: {COLORS["teal"]};
            --green: {COLORS["green"]};
            --coral: {COLORS["coral"]};
            --line: {COLORS["line"]};
            --surface: {COLORS["surface"]};
            --background: {COLORS["background"]};
        }}
        html, body, [class*="css"] {{
            font-family: "Inter", sans-serif;
            color: var(--ink);
            letter-spacing: 0;
        }}
        .stApp {{
            background:
                linear-gradient(180deg, rgba(20,108,110,.04) 0, transparent 240px),
                var(--background);
        }}
        h1, h2, h3 {{
            font-family: "Manrope", sans-serif;
            letter-spacing: 0;
        }}
        [data-testid="stSidebar"] {{
            background: #10272C;
            border-right: 1px solid rgba(255,255,255,.08);
        }}
        [data-testid="stSidebar"] * {{
            color: #EAF2F2;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{
            min-height: 42px;
            padding: 7px 10px;
            border-radius: 6px;
            transition: background .18s ease, transform .18s ease;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(255,255,255,.08);
            transform: translateX(2px);
        }}
        [data-testid="stSidebar"] [aria-checked="true"] {{
            background: rgba(38,154,120,.22);
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
            background: linear-gradient(112deg, #123E45 0%, #146C6E 60%, #269A78 100%);
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
            background: #7EF0C2;
            box-shadow: 0 0 0 4px rgba(126,240,194,.12);
            animation: pulse 1.8s infinite;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(6, minmax(150px, 1fr));
            gap: 12px;
            margin: 4px 0 20px;
        }}
        .kpi-card {{
            min-height: 112px;
            padding: 16px;
            background: rgba(255,255,255,.92);
            border: 1px solid var(--line);
            border-top: 3px solid var(--accent);
            border-radius: 8px;
            box-shadow: 0 7px 18px rgba(21,52,59,.06);
            transition: transform .18s ease, box-shadow .18s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 11px 24px rgba(21,52,59,.10);
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
            color: #2B7D63;
            font-size: 11px;
            font-weight: 600;
        }}
        .section-label {{
            margin: 8px 0 12px;
            color: var(--ink);
            font: 700 18px/1.3 "Manrope", sans-serif;
        }}
        .insight-row {{
            padding: 12px 0;
            border-bottom: 1px solid var(--line);
            color: #304149;
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
            color: #365057;
            background: #EEF5F5;
            border: 1px solid #D3E3E3;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}
        .assistant-note {{
            padding: 12px 14px;
            background: #EEF6F4;
            border-left: 3px solid var(--green);
            border-radius: 0 6px 6px 0;
            color: #31504B;
            font-size: 12px;
        }}
        .app-footer {{
            margin-top: 30px;
            padding: 18px 0 6px;
            border-top: 1px solid var(--line);
            color: var(--muted);
            text-align: center;
            font-size: 11px;
        }}
        div[data-testid="stMetric"] {{
            padding: 13px 14px;
            background: rgba(255,255,255,.94);
            border: 1px solid var(--line);
            border-radius: 8px;
        }}
        div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {{
            background: white;
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 6px 16px rgba(21,52,59,.04);
            overflow: hidden;
        }}
        .stButton > button, .stDownloadButton > button {{
            min-height: 38px;
            border-radius: 6px;
            font-weight: 600;
            transition: transform .16s ease, box-shadow .16s ease;
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
        @media (max-width: 1100px) {{
            .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }}
        }}
        @media (max-width: 700px) {{
            .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
            .product-header {{ min-height: 165px; padding: 20px; }}
            .product-title {{ font-size: 24px; }}
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .journey {{ grid-template-columns: repeat(2, 1fr); }}
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
            f'<div class="kpi-label">{escape(item["label"])}</div>'
            f'<div class="kpi-value">{escape(item["value"])}</div>'
            f'<div class="kpi-delta">{escape(item["delta"])}</div>'
            "</div>"
        )
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def style_figure(fig, height: int = 350):
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=52, b=18),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", color=COLORS["ink"], size=11),
        title_font=dict(family="Manrope", size=15, color=COLORS["ink"]),
        legend_title_text="",
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(gridcolor="#EDF1F2", zeroline=False)
    fig.update_yaxes(gridcolor="#EDF1F2", zeroline=False)
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


def executive_page(data: dict[str, pd.DataFrame], capacity: int) -> None:
    features, billing = data["features"], data["billing"]
    page_header(
        "Hospital Operations Intelligence Platform",
        "AI-driven healthcare analytics for faster, safer operational decisions.",
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

    left, right = st.columns([1, 1.35])
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
    with right:
        fig = px.area(
            monthly_revenue,
            x="claim_billing_date",
            y="paid_amount",
            title="Collected revenue trend",
            color_discrete_sequence=[COLORS["green"]],
        )
        st.plotly_chart(style_figure(fig), width="stretch")

    if not data["insights"].empty:
        section_title("Operational intelligence")
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
    cols = st.columns(6)
    values = [
        ("Age", f"{int(latest['age'])}"),
        ("Gender", str(latest["gender"])),
        ("Insurance", str(latest["insurance_category"])),
        ("Prior admissions", f"{int(latest['previous_admissions'])}"),
        ("Complexity index", f"{latest['patient_complexity_index']:.1f}"),
        ("Risk group", risk_class),
    ]
    for col, (label, value) in zip(cols, values):
        col.metric(label, value)
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
        fig = px.bar(
            department.sort_values("revenue"),
            x="revenue",
            y="department",
            color="success_rate",
            orientation="h",
            title="Revenue and outcome ranking",
            color_continuous_scale=["#E7B2A6", "#E9D18D", "#86CDB3"],
        )
        st.plotly_chart(style_figure(fig, 410), width="stretch")
    with right:
        matrix = department.set_index("department")[
            ["admissions", "revenue", "average_los", "average_wait", "success_rate"]
        ]
        normalized = (matrix - matrix.min()) / (matrix.max() - matrix.min())
        fig = px.imshow(
            normalized,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale=["#F4F7F8", "#70B7A3", "#146C6E"],
            title="Department performance matrix",
        )
        st.plotly_chart(style_figure(fig, 410), width="stretch")

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
        fig = px.line(
            forecast,
            x="forecast_date",
            y="display_occupancy_pct",
            title="ML occupancy forecast · next 90 days",
            color_discrete_sequence=[COLORS["blue"]],
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
            with st.form("readmission_prediction"):
                row, _ = model_input_form(features, "readmission")
                submit = st.form_submit_button("Analyze readmission risk")
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
                    st.metric("Risk classification", label)
                    st.metric("Estimated probability", f"{probability:.1%}")
                    st.info(
                        "Use this score to prioritize review and discharge follow-up. It does not replace clinical judgment."
                    )
    with tab_wait:
        if waiting_model is None:
            st.error("Waiting-time model artifact is unavailable.")
        else:
            with st.form("waiting_prediction"):
                row, _ = model_input_form(features, "waiting")
                submit = st.form_submit_button("Estimate waiting time")
            if submit:
                prediction = max(
                    0.0,
                    float(waiting_model.predict(row[model_columns(waiting_model)])[0]),
                )
                st.metric("Simulated waiting time", f"{prediction:.0f} minutes")
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
                submit = st.form_submit_button("Forecast revenue scenario")
            if submit:
                per_admission = max(
                    0.0,
                    float(revenue_model.predict(row[model_columns(revenue_model)])[0]),
                )
                total = per_admission * volume
                first, second, third = st.columns(3)
                first.metric("Per-admission revenue", f"${per_admission:,.0f}")
                second.metric("Patient volume", f"{volume:,}")
                third.metric("Expected revenue", f"${total:,.0f}")
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


def reports_page(data: dict[str, pd.DataFrame], capacity: int) -> None:
    page_header(
        "Reports and Assistant",
        "Generate executive reporting, download governed outputs, and ask operational questions.",
        "Decision distribution",
    )
    left, right = st.columns([1, 1.4])
    with left:
        section_title("Executive report")
        pdf_path = REPORTS / "executive_report.pdf"
        if st.button("Refresh executive PDF", type="primary", width="stretch"):
            with st.spinner("Analyzing hospital data and building the report..."):
                from src.generate_executive_report import main as generate_report

                generate_report()
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
    assistant_panel(data, capacity)


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
            Hospital Operations Intelligence Platform · Python · SQL · Machine Learning · Power BI · Streamlit<br>
            AI-driven healthcare decisions with transparent operational assumptions
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

    with st.spinner("Loading hospital intelligence..."):
        data = load_platform_data()
    if data["features"].empty:
        st.error("Processed hospital data is unavailable. Run `python src/data_pipeline.py`.")
        st.stop()

    with st.sidebar:
        st.image(str(LOGO), width=92)
        st.markdown("### Hospital AI Platform")
        st.caption("Operations command center")
        page = st.radio(
            "Navigation",
            [
                "📊 Executive Dashboard",
                "👥 Patient Analytics",
                "🩺 Doctor Performance",
                "🏢 Department Intelligence",
                "🛏 Bed Occupancy",
                "💰 Revenue Analytics",
                "🤖 AI Predictions",
                "🔍 Explainable AI",
                "📄 Reports",
                "⚙️ Settings",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(
            f"Source: {requested_data_source().upper()} · "
            f"{len(data['features']):,} admissions"
        )

    capacity = int(st.session_state.bed_capacity)
    routes = {
        "📊 Executive Dashboard": lambda: executive_page(data, capacity),
        "👥 Patient Analytics": lambda: patient_page(data),
        "🩺 Doctor Performance": lambda: doctor_page(data),
        "🏢 Department Intelligence": lambda: department_page(data),
        "🛏 Bed Occupancy": lambda: bed_page(data, capacity),
        "💰 Revenue Analytics": lambda: revenue_page(data),
        "🤖 AI Predictions": lambda: predictions_page(data),
        "🔍 Explainable AI": lambda: explainability_page(data),
        "📄 Reports": lambda: reports_page(data, capacity),
        "⚙️ Settings": lambda: settings_page(data),
    }
    routes[page]()
    footer()


if __name__ == "__main__":
    main()
