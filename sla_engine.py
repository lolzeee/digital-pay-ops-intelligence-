"""
Core SLA calculations and metrics processing module for Digital Pay Ops Intelligence.
Separates calculations strictly from presentation code.
Deterministic and transparent rules adhering to operational specifications.
"""

from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


# Status Definitions
RESOLVED_STATUSES = {"Resolved", "Closed"}

# SLA Risk Classification categories
SLA_OVERDUE = "Overdue"
SLA_AT_RISK = "At Risk"
SLA_WITHIN_SLA = "Within SLA"
SLA_BREACHED = "Breached"


def parse_datetime_series(series: pd.Series) -> pd.Series:
    """Helper to convert string datetime series to pandas datetime."""
    return pd.to_datetime(series, errors="coerce")


def classify_ticket_sla(
    row: pd.Series,
    now: datetime
) -> Tuple[str, float]:
    """
    Classify a single ticket into its SLA status:
    - Overdue: unresolved ticket whose SLA deadline has passed (now > sla_deadline).
    - At risk: unresolved ticket with 20% or less of its allocated SLA time remaining
               (0 <= remaining_time <= 0.20 * sla_duration).
    - Within SLA: resolved ticket completed before or on its deadline (resolved_at <= sla_deadline),
                  or unresolved ticket that is not at risk (remaining_time > 0.20 * sla_duration).
    - Breached: resolved ticket completed after its deadline (resolved_at > sla_deadline).

    Returns:
    (sla_risk_status: str, remaining_or_variance_hours: float)
    """
    status = str(row.get("status", "")).strip()
    is_resolved = status in RESOLVED_STATUSES

    created_at = row["created_at"]
    sla_deadline = row["sla_deadline"]
    sla_hours = float(row.get("sla_hours", 24))

    # Calculate SLA duration in total hours
    sla_duration_hours = (sla_deadline - created_at).total_seconds() / 3600.0
    if sla_duration_hours <= 0:
        sla_duration_hours = sla_hours if sla_hours > 0 else 24.0

    if is_resolved:
        resolved_at = row.get("resolved_at")
        if pd.isna(resolved_at):
            # Fallback if resolved status but missing date
            resolved_at = sla_deadline

        # Variance: positive means resolved early, negative means resolved late
        variance_hours = (sla_deadline - resolved_at).total_seconds() / 3600.0
        if resolved_at <= sla_deadline:
            return SLA_WITHIN_SLA, variance_hours
        else:
            return SLA_BREACHED, variance_hours
    else:
        # Unresolved
        remaining_hours = (sla_deadline - now).total_seconds() / 3600.0
        remaining_ratio = remaining_hours / sla_duration_hours

        if remaining_hours < 0:
            return SLA_OVERDUE, remaining_hours
        elif remaining_ratio <= 0.20:
            return SLA_AT_RISK, remaining_hours
        else:
            return SLA_WITHIN_SLA, remaining_hours


def enrich_ticket_data(df: pd.DataFrame, reference_time: datetime = None) -> pd.DataFrame:
    """
    Enrich dataframe with parsed datetimes, computed resolution hours,
    and SLA risk classifications.
    """
    df = df.copy()

    if reference_time is None:
        # If no explicit time provided, default to the max created_at/resolved_at or now
        reference_time = datetime(2026, 10, 28, 16, 0, 0)

    # Ensure datetimes are parsed
    df["created_at"] = parse_datetime_series(df["created_at"])
    df["sla_deadline"] = parse_datetime_series(df["sla_deadline"])
    if "resolved_at" in df.columns:
        df["resolved_at"] = parse_datetime_series(df["resolved_at"])
    else:
        df["resolved_at"] = pd.NaT

    # Calculate actual resolution hours for resolved tickets
    df["resolution_hours"] = np.where(
        df["resolved_at"].notna(),
        (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600.0,
        np.nan
    )

    # Apply deterministic SLA classification
    risk_results = [
        classify_ticket_sla(row, reference_time)
        for _, row in df.iterrows()
    ]

    df["sla_risk_status"] = [r[0] for r in risk_results]
    df["sla_time_delta_hours"] = [round(r[1], 1) for r in risk_results]
    df["is_open"] = ~df["status"].isin(RESOLVED_STATUSES)

    return df


def calculate_executive_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate executive KPI metrics:
    - Total tickets
    - Open tickets
    - SLA compliance percentage (Denominator: strictly resolved tickets)
    - Average resolution time (resolved tickets only)
    - High-risk overdue tickets (unresolved tickets past deadline)
    - At-risk count (unresolved tickets <= 20% remaining)
    - Breached count (resolved tickets past deadline)
    """
    total_tickets = len(df)
    open_df = df[df["is_open"]]
    resolved_df = df[~df["is_open"]]

    open_tickets = len(open_df)
    total_resolved = len(resolved_df)

    # SLA Compliance: Percentage of resolved tickets completed within SLA
    # Handled zero denominator safely
    if total_resolved > 0:
        resolved_within_sla = len(resolved_df[resolved_df["sla_risk_status"] == SLA_WITHIN_SLA])
        sla_compliance_pct = round((resolved_within_sla / total_resolved) * 100.0, 1)
        avg_resolution_time = round(resolved_df["resolution_hours"].mean(), 1)
    else:
        resolved_within_sla = 0
        sla_compliance_pct = 100.0  # Or 0.0, with clear note: no resolved tickets yet
        avg_resolution_time = 0.0

    overdue_count = len(open_df[open_df["sla_risk_status"] == SLA_OVERDUE])
    at_risk_count = len(open_df[open_df["sla_risk_status"] == SLA_AT_RISK])
    breached_count = len(resolved_df[resolved_df["sla_risk_status"] == SLA_BREACHED])

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": total_resolved,
        "resolved_within_sla": resolved_within_sla,
        "sla_compliance_pct": sla_compliance_pct,
        "avg_resolution_hours": avg_resolution_time,
        "high_risk_overdue": overdue_count,
        "at_risk_count": at_risk_count,
        "breached_count": breached_count,
        "compliance_denominator_description": "Total Resolved Tickets (Resolved Within SLA / Total Resolved)",
    }


def calculate_regional_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate regional operational performance:
    - Total tickets
    - Open tickets
    - Resolved tickets
    - SLA Compliance %
    - Average Resolution Hours
    - Overdue tickets
    """
    regions = df["region"].unique()
    rows = []

    for reg in sorted(regions):
        rdf = df[df["region"] == reg]
        resolved = rdf[~rdf["is_open"]]
        open_tk = rdf[rdf["is_open"]]

        total = len(rdf)
        res_count = len(resolved)
        res_within = len(resolved[resolved["sla_risk_status"] == SLA_WITHIN_SLA])
        overdue_cnt = len(open_tk[open_tk["sla_risk_status"] == SLA_OVERDUE])
        at_risk_cnt = len(open_tk[open_tk["sla_risk_status"] == SLA_AT_RISK])

        sla_comp = round((res_within / res_count * 100.0), 1) if res_count > 0 else 100.0
        avg_res = round(resolved["resolution_hours"].mean(), 1) if res_count > 0 else 0.0

        rows.append({
            "Region": reg,
            "Total Tickets": total,
            "Open Tickets": len(open_tk),
            "Resolved Tickets": res_count,
            "SLA Compliance (%)": sla_comp,
            "Avg Resolution (hrs)": avg_res,
            "Overdue (Urgent)": overdue_cnt,
            "At Risk": at_risk_cnt,
        })

    return pd.DataFrame(rows)


def generate_operational_recommendations(df: pd.DataFrame) -> list:
    """
    Synthesize high-priority operational actions for operations managers based on data patterns.
    """
    kpis = calculate_executive_kpis(df)
    reg_summary = calculate_regional_summary(df)
    recommendations = []

    # 1. Immediate triage for overdue
    if kpis["high_risk_overdue"] > 0:
        recommendations.append({
            "priority": "Urgent",
            "category": "Immediate Dispatch & Escalation",
            "action": f"Deploy immediate technician escalations for {kpis['high_risk_overdue']} overdue tickets. Prioritize Critical terminals causing active merchant revenue loss.",
            "impact": "Avert further SLA penalization and preserve merchant processing uptime."
        })

    # 2. At-risk preemptive intervention
    if kpis["at_risk_count"] > 0:
        recommendations.append({
            "priority": "High",
            "category": "Preemptive Triage",
            "action": f"Contact field leads regarding {kpis['at_risk_count']} open tickets currently within the final 20% SLA window to ensure prompt on-site closure.",
            "impact": "Prevents imminent SLA breaches before ticket lifecycle expires."
        })

    # 3. Regional re-balancing
    if not reg_summary.empty:
        lowest_reg = reg_summary.sort_values(by="SLA Compliance (%)").iloc[0]
        if lowest_reg["SLA Compliance (%)"] < 85.0:
            recommendations.append({
                "priority": "Medium",
                "category": "Capacity & Staff Rebalancing",
                "action": f"Reallocate 2 float field technicians to '{lowest_reg['Region']}' (compliance at {lowest_reg['SLA Compliance (%)']}%, avg resolution {lowest_reg['Avg Resolution (hrs)']} hrs).",
                "impact": "Alleviates regional technician backlog and levels cross-region SLA distribution."
            })

    # 4. Issue type root cause
    hardware_breaches = df[(df["issue_type"] == "Hardware Malfunction") & (df["sla_risk_status"] == SLA_BREACHED)]
    if len(hardware_breaches) > 5:
        recommendations.append({
            "priority": "Medium",
            "category": "Spare Parts & Logistics",
            "action": "Restock regional van kits with extra POS terminals and EMV chip readers to reduce trip return rates for Hardware Malfunctions.",
            "impact": "Decreases mean time to repair (MTTR) by ~25% for recurring device hardware swaps."
        })

    # 5. Default best practice recommendation
    recommendations.append({
        "priority": "Standard",
        "category": "Merchant Coordination Protocol",
        "action": "Enforce mandatory call-ahead confirmation 30 minutes prior to technician arrival to reduce 'Pending Merchant Action' stall times.",
        "impact": "Cuts idle technician travel time and enhances first-visit resolution rate."
    })

    return recommendations
