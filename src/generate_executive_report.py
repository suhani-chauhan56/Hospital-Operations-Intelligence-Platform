from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter, PercentFormatter

from project_config import config_value


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "processed"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"

INK = "#17242B"
MUTED = "#64747C"
TEAL = "#146C6E"
GREEN = "#269A78"
CORAL = "#D7644A"
GOLD = "#C9962B"
BLUE = "#3D6E8F"
LINE = "#DCE5E7"
SURFACE = "#F4F7F8"


def read_processed_table(
    name: str,
    **kwargs,
) -> pd.DataFrame:
    candidates = [DATA / f"{name}.csv.gz", DATA / f"{name}.csv"]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path, **kwargs)
    expected = " or ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Required report source is missing: {expected}")


def money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def add_header(
    fig: plt.Figure,
    title: str,
    subtitle: str,
    page: int,
    period: str,
    generated: str,
) -> None:
    fig.text(0.055, 0.945, title, fontsize=20, weight="bold", color=INK)
    fig.text(0.055, 0.91, subtitle, fontsize=9.5, color=MUTED)
    fig.text(
        0.945,
        0.945,
        f"PAGE {page}",
        ha="right",
        fontsize=8,
        weight="bold",
        color=TEAL,
    )
    fig.text(
        0.945,
        0.91,
        f"Period: {period}  |  Generated: {generated}",
        ha="right",
        fontsize=7.5,
        color=MUTED,
    )
    fig.add_artist(
        plt.Line2D([0.055, 0.945], [0.892, 0.892], color=LINE, linewidth=1)
    )


def add_footer(fig: plt.Figure, text: str) -> None:
    fig.add_artist(
        plt.Line2D([0.055, 0.945], [0.045, 0.045], color=LINE, linewidth=1)
    )
    fig.text(0.055, 0.022, text, fontsize=6.8, color=MUTED)
    fig.text(
        0.945,
        0.022,
        "Portfolio analytics | Not for clinical use",
        ha="right",
        fontsize=6.8,
        color=CORAL,
        weight="bold",
    )


def add_card(
    fig: plt.Figure,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    value: str,
    context: str,
    color: str,
) -> None:
    card = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.008,rounding_size=0.01",
        transform=fig.transFigure,
        facecolor="white",
        edgecolor=LINE,
        linewidth=1,
    )
    fig.add_artist(card)
    fig.add_artist(
        plt.Line2D(
            [x + 0.012, x + 0.012],
            [y + 0.02, y + height - 0.02],
            transform=fig.transFigure,
            color=color,
            linewidth=4,
            solid_capstyle="round",
        )
    )
    fig.text(x + 0.03, y + height - 0.035, label.upper(), fontsize=7.5, color=MUTED)
    fig.text(
        x + 0.03,
        y + 0.047,
        value,
        fontsize=17,
        weight="bold",
        color=INK,
    )
    fig.text(x + 0.03, y + 0.014, context, fontsize=7.3, color=color)


def style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(axis="y", color=LINE, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.title.set_color(INK)
    ax.title.set_fontsize(10)
    ax.title.set_weight("bold")


def load_metrics() -> dict[str, pd.DataFrame]:
    return {
        "readmission": pd.read_csv(REPORTS / "readmission_model_metrics.csv"),
        "waiting": pd.read_csv(REPORTS / "waiting_model_metrics.csv"),
        "revenue": pd.read_csv(REPORTS / "revenue_model_metrics.csv"),
        "occupancy": pd.read_csv(REPORTS / "occupancy_model_metrics.csv"),
    }


def main() -> None:
    features = read_processed_table(
        "model_features",
        parse_dates=["admit_date", "discharge_date"],
    )
    billing = read_processed_table(
        "billing",
        parse_dates=["claim_billing_date"],
    )
    claims = read_processed_table("claims")
    insurance = read_processed_table("insurance")
    forecast = pd.read_csv(REPORTS / "occupancy_forecast.csv")
    model_metrics = load_metrics()
    thresholds = config_value("executive_monitoring_thresholds")

    period_start = features["admit_date"].min()
    period_end = features["admit_date"].max()
    period = f"{period_start:%d %b %Y} - {period_end:%d %b %Y}"
    generated = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    latest_year = int(period_end.year)
    previous_year = latest_year - 1

    monthly = (
        features.set_index("admit_date")
        .resample("MS")
        .agg(
            admissions=("admission_id", "count"),
            readmission_rate=("readmitted_30d", "mean"),
            average_los=("los_days", "mean"),
        )
        .reset_index()
    )
    yearly = (
        features.assign(year=features["admit_date"].dt.year)
        .groupby("year")
        .agg(
            admissions=("admission_id", "count"),
            readmission_rate=("readmitted_30d", "mean"),
            average_los=("los_days", "mean"),
        )
    )
    current = yearly.loc[latest_year]
    previous = yearly.loc[previous_year]
    admission_delta = current["admissions"] / previous["admissions"] - 1
    readmission_delta = (
        current["readmission_rate"] - previous["readmission_rate"]
    )

    ward = (
        features.groupby("ward_type")
        .agg(
            admissions=("admission_id", "count"),
            readmissions=("readmitted_30d", "sum"),
            readmission_rate=("readmitted_30d", "mean"),
            average_los=("los_days", "mean"),
        )
        .sort_values("readmission_rate")
    )
    admit_type = (
        features.groupby("admit_type")
        .agg(
            admissions=("admission_id", "count"),
            readmission_rate=("readmitted_30d", "mean"),
        )
        .sort_values("readmission_rate")
    )
    high_threshold = features["patient_complexity_index"].quantile(0.75)
    high_complexity = features[
        features["patient_complexity_index"] >= high_threshold
    ]

    finance = billing.merge(insurance, on="insurance_id", how="left")
    payer = (
        finance.groupby("insurance_provider")
        .agg(
            claims=("billing_id", "count"),
            billed=("billed_amount", "sum"),
            paid=("paid_amount", "sum"),
            gap=("claim_gap", "sum"),
        )
        .sort_values("paid")
    )
    payer["collection_rate"] = payer["paid"] / payer["billed"]
    monthly_revenue = (
        finance.set_index("claim_billing_date")
        .resample("MS")
        .agg(billed=("billed_amount", "sum"), paid=("paid_amount", "sum"))
        .reset_index()
    )
    claim_status = claims["claim_status"].value_counts()
    total_billed = billing["billed_amount"].sum()
    total_paid = billing["paid_amount"].sum()
    collection_rate = total_paid / total_billed
    approval_rate = claims["claim_approved"].mean()
    occupancy_30 = float(
        forecast.loc[forecast["horizon_days"] == 30, "forecast_occupancy_pct"].iloc[0]
    )

    action_plan = pd.DataFrame(
        [
            {
                "priority": "P1",
                "action": "Review ICU readmissions and discharge follow-up workflow",
                "owner": "Clinical Quality Lead",
                "timeframe": "30 days",
                "success_measure": "Root-cause review completed; approved ward target established",
                "evidence": f"ICU readmission {ward.loc['ICU', 'readmission_rate']:.1%}",
            },
            {
                "priority": "P1",
                "action": "Analyze payer collection leakage and denied claims",
                "owner": "Revenue Cycle Manager",
                "timeframe": "30 days",
                "success_measure": (
                    f"Collection rate monitored against illustrative "
                    f"{thresholds['claim_collection_rate']:.0%} threshold"
                ),
                "evidence": f"Current collection rate {collection_rate:.1%}",
            },
            {
                "priority": "P2",
                "action": "Capture real arrival, triage, and service timestamps",
                "owner": "Operations Data Owner",
                "timeframe": "60 days",
                "success_measure": "Observed queue timestamps pass completeness checks",
                "evidence": "Current waiting target is simulated",
            },
            {
                "priority": "P2",
                "action": "Replace surrogate claim links and derived master data",
                "owner": "Data Governance Lead",
                "timeframe": "90 days",
                "success_measure": "Governed encounter, provider, department, and patient keys",
                "evidence": "Source files have no shared encounter key",
            },
        ]
    )
    action_plan.to_csv(REPORTS / "executive_action_plan.csv", index=False)

    with PdfPages(REPORTS / "executive_report.pdf") as pdf:
        # Page 1: executive summary
        fig = plt.figure(figsize=(11.7, 8.3), facecolor="white")
        add_header(
            fig,
            "Hospital Operations Intelligence",
            "Executive decision brief | Observed KPIs lead; assumptions are explicitly labelled",
            1,
            period,
            generated,
        )
        cards = [
            (
                "Admissions",
                f"{len(features):,}",
                f"{latest_year}: {int(current['admissions']):,} ({admission_delta:+.1%} YoY)",
                TEAL,
            ),
            (
                "Patients",
                f"{features['patient_id'].nunique():,}",
                "Unique source patient identifiers",
                BLUE,
            ),
            (
                "Readmission",
                f"{features['readmitted_30d'].mean():.1%}",
                f"{latest_year} YoY change {readmission_delta:+.1%}",
                CORAL,
            ),
            (
                "Average LOS",
                f"{features['los_days'].mean():.1f} days",
                f"{latest_year}: {current['average_los']:.1f} days",
                GOLD,
            ),
            (
                "Collected revenue",
                money(total_paid),
                f"{collection_rate:.1%} of {money(total_billed)} billed",
                GREEN,
            ),
            (
                "30-day occupancy",
                f"{occupancy_30:.1f}%",
                "Forecast | 500-bed portfolio assumption",
                BLUE,
            ),
        ]
        positions = [
            (0.055, 0.70),
            (0.355, 0.70),
            (0.655, 0.70),
            (0.055, 0.55),
            (0.355, 0.55),
            (0.655, 0.55),
        ]
        for (label, value, context, color), (x, y) in zip(cards, positions):
            add_card(fig, x, y, 0.275, 0.12, label, value, context, color)

        fig.text(0.055, 0.485, "DECISION PRIORITIES", fontsize=9, weight="bold", color=TEAL)
        priorities = [
            (
                "1",
                "ICU readmission review",
                f"{ward.loc['ICU', 'readmissions']:,.0f} of "
                f"{ward.loc['ICU', 'admissions']:,.0f} ICU encounters were "
                f"readmitted within 30 days ({ward.loc['ICU', 'readmission_rate']:.1%}).",
                "Clinical Quality Lead | 30 days",
            ),
            (
                "2",
                "Revenue-cycle leakage",
                f"Collected {collection_rate:.1%} of billed value. Approval is "
                f"{approval_rate:.1%}, showing that approval and collection are different controls.",
                "Revenue Cycle Manager | 30 days",
            ),
            (
                "3",
                "Operational data readiness",
                "Waiting time is simulated and admission-level revenue is surrogate-linked. "
                "Replace these fields before operational deployment.",
                "Operations Data Owner | 60-90 days",
            ),
        ]
        y = 0.415
        for number, title, body, owner in priorities:
            fig.text(
                0.06,
                y,
                number,
                fontsize=14,
                weight="bold",
                color="white",
                bbox={"boxstyle": "circle,pad=0.35", "facecolor": TEAL, "edgecolor": "none"},
            )
            fig.text(0.105, y + 0.012, title, fontsize=10, weight="bold", color=INK)
            fig.text(0.105, y - 0.022, fill(body, 112), fontsize=8.3, color=MUTED)
            fig.text(0.105, y - 0.055, owner, fontsize=7.5, color=TEAL, weight="bold")
            y -= 0.115
        add_footer(
            fig,
            "Sources: supplied admissions and claims CSVs. Revenue is aggregate claims evidence; occupancy uses observed census and an assumed capacity.",
        )
        pdf.savefig(fig, facecolor=fig.get_facecolor())
        plt.close(fig)

        # Page 2: patient flow and outcomes
        fig, axes = plt.subplots(2, 2, figsize=(11.7, 8.3), facecolor="white")
        fig.subplots_adjust(left=0.07, right=0.95, top=0.84, bottom=0.10, hspace=0.42, wspace=0.28)
        add_header(
            fig,
            "Patient Flow and Outcomes",
            "Observed admissions, length of stay, and readmission outcomes",
            2,
            period,
            generated,
        )
        recent = monthly.tail(24)
        axes[0, 0].plot(recent["admit_date"], recent["admissions"], color=TEAL, linewidth=2)
        axes[0, 0].plot(
            recent["admit_date"],
            recent["admissions"].rolling(3).mean(),
            color=GOLD,
            linewidth=1.5,
            linestyle="--",
            label="3-month average",
        )
        axes[0, 0].set_title("Monthly admissions | Latest 24 months")
        axes[0, 0].legend(frameon=False, fontsize=7)
        style_axis(axes[0, 0])

        axes[0, 1].barh(ward.index, ward["readmission_rate"], color=CORAL)
        axes[0, 1].axvline(
            thresholds["readmission_rate"],
            color=INK,
            linestyle="--",
            linewidth=1.2,
            label=f"Illustrative threshold {thresholds['readmission_rate']:.0%}",
        )
        axes[0, 1].xaxis.set_major_formatter(PercentFormatter(1))
        axes[0, 1].set_title("30-day readmission by observed ward")
        axes[0, 1].legend(frameon=False, fontsize=7, loc="upper right")
        for index, value in enumerate(ward["readmission_rate"]):
            axes[0, 1].text(value + 0.004, index, f"{value:.1%}", va="center", fontsize=7)
        style_axis(axes[0, 1])

        axes[1, 0].barh(ward.index, ward["average_los"], color=BLUE)
        axes[1, 0].set_title("Average LOS by observed ward")
        axes[1, 0].set_xlabel("Days")
        for index, value in enumerate(ward["average_los"]):
            axes[1, 0].text(value + 0.15, index, f"{value:.1f}", va="center", fontsize=7)
        style_axis(axes[1, 0])

        axes[1, 1].barh(admit_type.index, admit_type["readmission_rate"], color=GREEN)
        axes[1, 1].xaxis.set_major_formatter(PercentFormatter(1))
        axes[1, 1].set_title("Readmission by observed admission type")
        for index, value in enumerate(admit_type["readmission_rate"]):
            axes[1, 1].text(value + 0.003, index, f"{value:.1%}", va="center", fontsize=7)
        style_axis(axes[1, 1])
        add_footer(
            fig,
            f"Illustrative readmission threshold is not hospital-approved. High-complexity score >= {high_threshold:.0f}: "
            f"{len(high_complexity):,} encounters, {high_complexity['readmitted_30d'].mean():.1%} readmission.",
        )
        pdf.savefig(fig, facecolor=fig.get_facecolor())
        plt.close(fig)

        # Page 3: financial and claims performance
        fig, axes = plt.subplots(2, 2, figsize=(11.7, 8.3), facecolor="white")
        fig.subplots_adjust(left=0.07, right=0.95, top=0.84, bottom=0.11, hspace=0.42, wspace=0.30)
        add_header(
            fig,
            "Financial and Claims Performance",
            "Observed aggregate claims evidence | No audited admission-level attribution",
            3,
            f"{billing['claim_billing_date'].min():%d %b %Y} - {billing['claim_billing_date'].max():%d %b %Y}",
            generated,
        )
        recent_revenue = monthly_revenue.tail(24)
        axes[0, 0].plot(
            recent_revenue["claim_billing_date"],
            recent_revenue["billed"],
            color=GOLD,
            linewidth=1.6,
            label="Billed",
        )
        axes[0, 0].plot(
            recent_revenue["claim_billing_date"],
            recent_revenue["paid"],
            color=GREEN,
            linewidth=2,
            label="Paid",
        )
        axes[0, 0].yaxis.set_major_formatter(
            FuncFormatter(lambda value, _: money(value))
        )
        axes[0, 0].set_title("Monthly billed versus paid | Latest 24 months")
        axes[0, 0].legend(frameon=False, fontsize=7)
        style_axis(axes[0, 0])

        axes[0, 1].barh(payer.index, payer["collection_rate"], color=GREEN)
        axes[0, 1].axvline(
            thresholds["claim_collection_rate"],
            color=INK,
            linestyle="--",
            linewidth=1.2,
            label=f"Illustrative threshold {thresholds['claim_collection_rate']:.0%}",
        )
        axes[0, 1].xaxis.set_major_formatter(PercentFormatter(1))
        axes[0, 1].set_xlim(0, max(0.75, payer["collection_rate"].max() + 0.05))
        axes[0, 1].set_title("Collection rate by observed payer")
        axes[0, 1].legend(frameon=False, fontsize=7, loc="lower right")
        style_axis(axes[0, 1])

        axes[1, 0].barh(payer.index, payer["gap"], color=CORAL)
        axes[1, 0].xaxis.set_major_formatter(
            FuncFormatter(lambda value, _: money(value))
        )
        axes[1, 0].set_title("Billed-to-paid gap by payer")
        style_axis(axes[1, 0])

        axes[1, 1].bar(
            claim_status.index.astype(str),
            claim_status.values,
            color=[TEAL, CORAL, GOLD][: len(claim_status)],
        )
        axes[1, 1].set_title("Observed claim status distribution")
        axes[1, 1].tick_params(axis="x", rotation=20)
        style_axis(axes[1, 1])
        add_footer(
            fig,
            f"Claims: {len(billing):,} rows versus {len(features):,} admissions. "
            f"Overall approval {approval_rate:.1%}; collection {collection_rate:.1%}. "
            "A surrogate link is used only for portfolio workflow demonstration.",
        )
        pdf.savefig(fig, facecolor=fig.get_facecolor())
        plt.close(fig)

        # Page 4: model governance and accountable action plan
        fig = plt.figure(figsize=(11.7, 8.3), facecolor="white")
        add_header(
            fig,
            "Decision Governance and Delivery Plan",
            "Core analytical evidence is separated from sandbox demonstrations",
            4,
            period,
            generated,
        )
        fig.text(0.055, 0.85, "MODEL READINESS", fontsize=9, weight="bold", color=TEAL)
        model_rows = [
            [
                "Readmission",
                "Core analytical",
                f"ROC AUC {model_metrics['readmission'].iloc[0]['roc_auc']:.3f}",
                "Observed",
                "Screening research only",
            ],
            [
                "Bed occupancy",
                "Core analytical",
                f"MAE {model_metrics['occupancy'].iloc[0]['MAE']:.2f} beds",
                "Observed census + capacity assumption",
                "Capacity scenario",
            ],
            [
                "Waiting time",
                "Sandbox",
                f"RMSE {model_metrics['waiting'].iloc[0]['RMSE']:.3f} min",
                "Simulated formula",
                "Pipeline demonstration",
            ],
            [
                "Revenue",
                "Sandbox",
                f"R2 {model_metrics['revenue'].iloc[0]['R2']:.3f}",
                "Surrogate + simulated",
                "Scenario demonstration",
            ],
        ]
        model_ax = fig.add_axes([0.055, 0.61, 0.89, 0.21])
        model_ax.axis("off")
        table = model_ax.table(
            cellText=model_rows,
            colLabels=["Model", "Portfolio tier", "Holdout result", "Target provenance", "Decision use"],
            cellLoc="left",
            colLoc="left",
            loc="upper left",
            bbox=[0, 0, 1, 1],
            colWidths=[0.14, 0.16, 0.16, 0.27, 0.27],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.2)
        for (row, _), cell in table.get_celld().items():
            cell.set_edgecolor(LINE)
            cell.set_linewidth(0.7)
            if row == 0:
                cell.set_facecolor(INK)
                cell.get_text().set_color("white")
                cell.get_text().set_weight("bold")
            elif row in (1, 2):
                cell.set_facecolor("#EAF4F1")
            else:
                cell.set_facecolor("#FFF6E5")

        fig.text(0.055, 0.56, "ACCOUNTABLE ACTION PLAN", fontsize=9, weight="bold", color=TEAL)
        action_ax = fig.add_axes([0.055, 0.20, 0.89, 0.33])
        action_ax.axis("off")
        action_rows = [
            [
                row.priority,
                fill(row.action, 37),
                row.owner,
                row.timeframe,
                fill(row.success_measure, 42),
            ]
            for row in action_plan.itertuples(index=False)
        ]
        table = action_ax.table(
            cellText=action_rows,
            colLabels=["Priority", "Action", "Owner", "Timeframe", "Success measure"],
            cellLoc="left",
            colLoc="left",
            loc="upper left",
            bbox=[0, 0, 1, 1],
            colWidths=[0.08, 0.30, 0.19, 0.11, 0.32],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.1)
        for (row, _), cell in table.get_celld().items():
            cell.set_edgecolor(LINE)
            cell.set_linewidth(0.7)
            if row == 0:
                cell.set_facecolor(INK)
                cell.get_text().set_color("white")
                cell.get_text().set_weight("bold")
            elif row % 2:
                cell.set_facecolor(SURFACE)
            cell.get_text().set_wrap(True)

        fig.text(0.055, 0.145, "DERIVED DIMENSIONS", fontsize=8, weight="bold", color=CORAL)
        fig.text(
            0.055,
            0.112,
            fill(
                "Doctor, department, demographics, medicine, appointment, waiting-time, "
                "and admission-claim relationships are deterministic portfolio constructs. "
                "Observed hospital, ward, dates, clinical fields, readmission, payer, and "
                "aggregate billing evidence lead all executive conclusions.",
                165,
            ),
            fontsize=7.8,
            color=MUTED,
        )
        add_footer(
            fig,
            "Monitoring thresholds are illustrative portfolio controls, not approved hospital policy. "
            "See reports/feature_provenance.csv and docs/DATA_GOVERNANCE.md.",
        )
        pdf.savefig(fig, facecolor=fig.get_facecolor())
        plt.close(fig)

    print("Executive PDF report saved: 4 decision-ready pages.")


if __name__ == "__main__":
    main()
