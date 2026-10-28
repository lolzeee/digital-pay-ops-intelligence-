"""
Digital Pay Ops Intelligence - Enterprise POS Operations Dashboard.
Interactive Streamlit Web Application for Field-Service & Terminal Management.

Pages:
1. Executive Overview
2. Ticket Explorer
3. SLA Risk Monitor
4. Regional Insights
5. Methodology & Compliance
"""

from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from data_generator import ensure_dataset
from sla_engine import (
    enrich_ticket_data,
    calculate_executive_kpis,
    calculate_regional_summary,
    generate_operational_recommendations,
    SLA_OVERDUE,
    SLA_AT_RISK,
    SLA_WITHIN_SLA,
    SLA_BREACHED,
)

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Digital Pay Ops Intelligence | Field Operations",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Custom Fintech Enterprise CSS Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global Typography & Font hierarchy */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Clean, high-contrast banner */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }
    .app-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .app-subtitle {
        font-size: 0.90rem;
        color: #94a3b8;
        line-height: 1.4;
    }
    .badge-synthetic {
        display: inline-block;
        background-color: #3b82f6;
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* KPI metric cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .kpi-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 4px;
    }

    /* Risk status tags */
    .status-pill {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        text-align: center;
    }
    .pill-overdue { background-color: #fee2e2; color: #991b1b; }
    .pill-at-risk { background-color: #fef3c7; color: #92400e; }
    .pill-within { background-color: #dcfce7; color: #166534; }
    .pill-breached { background-color: #fce7f3; color: #9d174d; }

    /* Action boxes */
    .action-card {
        background: #0f172a;
        border-left: 4px solid #3b82f6;
        border-top: 1px solid #1e293b;
        border-right: 1px solid #1e293b;
        border-bottom: 1px solid #1e293b;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .action-card.urgent { border-left-color: #ef4444; }
    .action-card.high { border-left-color: #f59e0b; }
    .action-card.medium { border-left-color: #3b82f6; }
    .action-card.standard { border-left-color: #10b981; }

    .action-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
    }
    .action-desc {
        font-size: 0.85rem;
        color: #cbd5e1;
        line-height: 1.4;
    }
    .action-impact {
        font-size: 0.80rem;
        color: #94a3b8;
        font-style: italic;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Data Loader and Processing
# ---------------------------------------------------------
REFERENCE_SNAPSHOT_TIME = datetime(2026, 10, 28, 16, 0, 0)

@st.cache_data
def get_ops_data():
    raw_df = ensure_dataset("synthetic_pos_tickets.csv", reference_time=REFERENCE_SNAPSHOT_TIME)
    enriched_df = enrich_ticket_data(raw_df, reference_time=REFERENCE_SNAPSHOT_TIME)
    return enriched_df

df = get_ops_data()


# ---------------------------------------------------------
# Sidebar Navigation & Filter State
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 💳 **Digital Pay Ops**")
    st.markdown("<span class='badge-synthetic'>Synthetic Concept Data</span>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.8rem; color: #94a3b8; margin-top: 4px;'>POS Terminal & Field Operations</p>", unsafe_allow_html=True)
    st.markdown("---")

    selected_page = st.radio(
        "Navigation",
        [
            "1. Executive Overview",
            "2. Ticket Explorer",
            "3. SLA Risk Monitor",
            "4. Regional Insights",
            "5. Methodology & SLA Spec",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("#### **Operational Snapshot Context**")
    st.caption(f"**Audit Time:** {REFERENCE_SNAPSHOT_TIME.strftime('%Y-%m-%d %H:%M')}")
    st.caption("**Dataset Size:** 320 Field Tickets")
    st.caption("**Data Source:** Synthetic POS field-service model")

    st.markdown("---")
    st.info("💡 **Independent Portfolio Concept**: Inspired by publicly known fintech merchant ops. Unaffiliated with any entity.")


# ---------------------------------------------------------
# Header Component
# ---------------------------------------------------------
def render_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="app-header">
        <div class="app-title">{title}</div>
        <div class="app-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# PAGE 1: EXECUTIVE OVERVIEW
# =========================================================
if selected_page == "1. Executive Overview":
    render_header(
        "Executive Operations Overview",
        "High-level operational cockpit monitoring POS terminal installations, technician field SLAs, and triage action items."
    )

    kpis = calculate_executive_kpis(df)

    # Top KPI metric cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Tickets", f"{kpis['total_tickets']}")
    with col2:
        st.metric("Open Tickets", f"{kpis['open_tickets']}", delta=f"{round(kpis['open_tickets']/kpis['total_tickets']*100, 1)}% of total", delta_color="off")
    with col3:
        st.metric("SLA Compliance", f"{kpis['sla_compliance_pct']}%", delta=f"{kpis['resolved_within_sla']} / {kpis['resolved_tickets']} resolved")
    with col4:
        st.metric("Avg Resolution Time", f"{kpis['avg_resolution_hours']} hrs", delta="Resolved tickets", delta_color="off")
    with col5:
        st.metric("High-Risk Overdue", f"{kpis['high_risk_overdue']}", delta="Immediate Triage", delta_color="inverse")

    st.markdown("---")

    # Layout: Trend over time and Regional comparison
    row2_col1, row2_col2 = st.columns([3, 2])

    with row2_col1:
        st.subheader("📈 Ticket Volume & Inflow Trend")
        df_trend = df.copy()
        df_trend["created_date"] = df_trend["created_at"].dt.date
        trend_summary = df_trend.groupby(["created_date", "status"]).size().reset_index(name="count")

        fig_trend = px.bar(
            trend_summary,
            x="created_date",
            y="count",
            color="status",
            title="Daily Ticket Volume by Current Status",
            labels={"created_date": "Date Created", "count": "Tickets", "status": "Status"},
            color_discrete_map={
                "Resolved": "#10b981",
                "In Progress": "#3b82f6",
                "Dispatched": "#f59e0b",
                "Pending Merchant Action": "#a855f7"
            },
            template="plotly_dark",
        )
        fig_trend.update_layout(
            barmode="stack",
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20),
            height=340
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with row2_col2:
        st.subheader("🌍 Regional Compliance Comparison")
        reg_summary = calculate_regional_summary(df)

        fig_reg = px.bar(
            reg_summary,
            x="Region",
            y="SLA Compliance (%)",
            text="SLA Compliance (%)",
            color="SLA Compliance (%)",
            color_continuous_scale="Tealgrn",
            title="SLA Compliance Rate by Region",
            template="plotly_dark",
        )
        fig_reg.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_reg.update_layout(
            yaxis=dict(range=[50, 105]),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=50, b=20),
            height=340
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown("---")

    # Recommended Operational Actions
    st.subheader("🎯 Prioritized Operational Actions")
    st.caption("Deterministic recommendations synthesized from SLA compliance, open backlog, and regional stress points.")

    actions = generate_operational_recommendations(df)
    for act in actions:
        p_class = act["priority"].lower()
        st.markdown(f"""
        <div class="action-card {p_class}">
            <div class="action-title">
                <span>{act['category']}</span>
                <span style="font-size: 0.8rem; text-transform: uppercase;">[{act['priority']} Priority]</span>
            </div>
            <div class="action-desc">{act['action']}</div>
            <div class="action-impact"><strong>Expected Impact:</strong> {act['impact']}</div>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# PAGE 2: TICKET EXPLORER
# =========================================================
elif selected_page == "2. Ticket Explorer":
    render_header(
        "Field Ticket Explorer",
        "Detailed granular ticket registry with multi-dimensional filtering, SLA risk indicators, and search capabilities."
    )

    # Filter Bar
    with st.expander("🔍 Filter Controls", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)

        with fcol1:
            all_regions = ["All Regions"] + sorted(list(df["region"].unique()))
            sel_region = st.selectbox("Region", all_regions)

        with fcol2:
            all_statuses = ["All Statuses"] + sorted(list(df["status"].unique()))
            sel_status = st.selectbox("Status", all_statuses)

        with fcol3:
            all_issues = ["All Issue Types"] + sorted(list(df["issue_type"].unique()))
            sel_issue = st.selectbox("Issue Type", all_issues)

        with fcol4:
            all_priorities = ["All Priorities"] + ["Critical", "High", "Medium", "Low"]
            sel_priority = st.selectbox("Priority", all_priorities)

        search_query = st.text_input("🔎 Search by Ticket ID or Assigned Technician", placeholder="e.g. TICK-1015 or Al-Harbi")

    # Filter evaluation
    filtered_df = df.copy()
    if sel_region != "All Regions":
        filtered_df = filtered_df[filtered_df["region"] == sel_region]
    if sel_status != "All Statuses":
        filtered_df = filtered_df[filtered_df["status"] == sel_status]
    if sel_issue != "All Issue Types":
        filtered_df = filtered_df[filtered_df["issue_type"] == sel_issue]
    if sel_priority != "All Priorities":
        filtered_df = filtered_df[filtered_df["priority"] == sel_priority]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["ticket_id"].str.lower().contains(q, na=False) |
            filtered_df["assigned_technician"].str.lower().contains(q, na=False)
        ]

    # Metrics on filtered view
    scol1, scol2, scol3, scol4 = st.columns(4)
    scol1.metric("Matching Tickets", len(filtered_df))
    scol2.metric("Overdue in Selection", len(filtered_df[filtered_df["sla_risk_status"] == SLA_OVERDUE]))
    scol3.metric("At Risk in Selection", len(filtered_df[filtered_df["sla_risk_status"] == SLA_AT_RISK]))
    scol4.metric("Breached in Selection", len(filtered_df[filtered_df["sla_risk_status"] == SLA_BREACHED]))

    # Display Table
    st.markdown("### Ticket Records")

    # Format display columns
    display_df = filtered_df[[
        "ticket_id",
        "region",
        "issue_type",
        "priority",
        "status",
        "sla_risk_status",
        "assigned_technician",
        "created_at",
        "sla_deadline",
        "resolved_at",
    ]].copy()

    display_df.rename(columns={
        "ticket_id": "Ticket ID",
        "region": "Region",
        "issue_type": "Issue Type",
        "priority": "Priority",
        "status": "Ticket Status",
        "sla_risk_status": "SLA Risk Indicator",
        "assigned_technician": "Technician",
        "created_at": "Created Time",
        "sla_deadline": "SLA Deadline",
        "resolved_at": "Resolved Time",
    }, inplace=True)

    # Style highlighting (supports both pandas map and legacy applymap)
    def highlight_sla(val):
        if val == SLA_OVERDUE:
            return "background-color: #7f1d1d; color: #ffffff; font-weight: bold;"
        elif val == SLA_AT_RISK:
            return "background-color: #78350f; color: #fde68a; font-weight: bold;"
        elif val == SLA_BREACHED:
            return "background-color: #701a75; color: #fbcfe8; font-weight: bold;"
        elif val == SLA_WITHIN_SLA:
            return "background-color: #064e3b; color: #a7f3d0;"
        return ""

    if hasattr(display_df.style, "map"):
        styled_table = display_df.style.map(highlight_sla, subset=["SLA Risk Indicator"])
    else:
        styled_table = display_df.style.applymap(highlight_sla, subset=["SLA Risk Indicator"])
    st.dataframe(styled_table, use_container_width=True, height=450)

    # CSV Download option
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Tickets (CSV)",
        data=csv_bytes,
        file_name="digital_pay_pos_tickets_filtered.csv",
        mime="text/csv"
    )


# =========================================================
# PAGE 3: SLA RISK MONITOR
# =========================================================
elif selected_page == "3. SLA Risk Monitor":
    render_header(
        "Deterministic SLA Risk Monitor",
        "Transparent operational classification rules for terminal dispatch. Real-time detection of overdue and impending breaches."
    )

    # Formula & Denominator definition callout
    st.markdown("""
    <div style="background: #1e293b; border: 1px solid #3b82f6; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
        <h4 style="color: #60a5fa; margin: 0 0 8px 0;">📐 Deterministic SLA Specification & Exact Formula</h4>
        <p style="color: #cbd5e1; font-size: 0.88rem; margin: 0 0 8px 0;">
            SLA compliance is calculated strictly on closed resolution lifecycles to avoid early-stage bias:
        </p>
        <div style="background: #0f172a; padding: 10px 14px; border-radius: 6px; font-family: monospace; font-size: 0.95rem; color: #38bdf8;">
            SLA Compliance (%) = [ Resolved Tickets Completed Before Deadline / Total Resolved Tickets ] × 100
        </div>
        <p style="color: #94a3b8; font-size: 0.80rem; margin: 8px 0 0 0;">
            • <strong>Denominator:</strong> Strictly resolved tickets (Resolved or Closed). Unresolved tickets are monitored separately in the backlog.<br/>
            • <strong>Zero Handling:</strong> In cases with 0 resolved tickets, compliance defaults to 100% with an explicit notification.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # SLA Categories Breakdown
    kpis = calculate_executive_kpis(df)
    rcol1, rcol2, rcol3, rcol4 = st.columns(4)

    with rcol1:
        st.markdown("""
        <div class="kpi-card" style="border-top: 4px solid #ef4444;">
            <div class="kpi-title">🔴 Overdue</div>
            <div class="kpi-value" style="color: #f87171;">{}</div>
            <div class="kpi-sub">Unresolved & Past Deadline</div>
        </div>
        """.format(kpis['high_risk_overdue']), unsafe_allow_html=True)

    with rcol2:
        st.markdown("""
        <div class="kpi-card" style="border-top: 4px solid #f59e0b;">
            <div class="kpi-title">🟡 At Risk</div>
            <div class="kpi-value" style="color: #fbbf24;">{}</div>
            <div class="kpi-sub">Unresolved, ≤ 20% Time Left</div>
        </div>
        """.format(kpis['at_risk_count']), unsafe_allow_html=True)

    with rcol3:
        st.markdown("""
        <div class="kpi-card" style="border-top: 4px solid #10b981;">
            <div class="kpi-title">🟢 Within SLA</div>
            <div class="kpi-value" style="color: #34d399;">{}</div>
            <div class="kpi-sub">Resolved on-time or safe open</div>
        </div>
        """.format(len(df[df["sla_risk_status"] == SLA_WITHIN_SLA])), unsafe_allow_html=True)

    with rcol4:
        st.markdown("""
        <div class="kpi-card" style="border-top: 4px solid #ec4899;">
            <div class="kpi-title">🟣 Breached</div>
            <div class="kpi-value" style="color: #f472b6;">{}</div>
            <div class="kpi-sub">Resolved After Deadline</div>
        </div>
        """.format(kpis['breached_count']), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Detailed breakdown view
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Distribution by SLA Status")
        status_dist = df["sla_risk_status"].value_counts().reset_index()
        status_dist.columns = ["SLA Category", "Count"]

        fig_pie = px.pie(
            status_dist,
            names="SLA Category",
            values="Count",
            hole=0.45,
            color="SLA Category",
            color_discrete_map={
                SLA_OVERDUE: "#ef4444",
                SLA_AT_RISK: "#f59e0b",
                SLA_WITHIN_SLA: "#10b981",
                SLA_BREACHED: "#d946ef",
            },
            template="plotly_dark",
        )
        fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.subheader("Risk Distribution Across Issue Types")
        issue_risk = df.groupby(["issue_type", "sla_risk_status"]).size().reset_index(name="count")
        fig_bar = px.bar(
            issue_risk,
            x="issue_type",
            y="count",
            color="sla_risk_status",
            barmode="group",
            labels={"issue_type": "POS Issue Category", "count": "Tickets", "sla_risk_status": "SLA Status"},
            color_discrete_map={
                SLA_OVERDUE: "#ef4444",
                SLA_AT_RISK: "#f59e0b",
                SLA_WITHIN_SLA: "#10b981",
                SLA_BREACHED: "#d946ef",
            },
            template="plotly_dark",
        )
        fig_bar.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20), xaxis_tickangle=-25)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Urgent High-Risk Focus Table
    st.subheader("⚠️ High-Risk Backlog (Overdue & Imminent Risk)")
    urgent_df = df[df["sla_risk_status"].isin([SLA_OVERDUE, SLA_AT_RISK])].sort_values(
        by="sla_time_delta_hours", ascending=True
    )

    if urgent_df.empty:
        st.success("No active overdue or at-risk tickets! Field dispatch operations are running within all SLA windows.")
    else:
        st.dataframe(
            urgent_df[[
                "ticket_id", "region", "priority", "issue_type", "status",
                "assigned_technician", "sla_deadline", "sla_time_delta_hours"
            ]].rename(columns={
                "ticket_id": "Ticket ID",
                "region": "Region",
                "priority": "Priority",
                "issue_type": "Issue Type",
                "status": "Current Status",
                "assigned_technician": "Technician",
                "sla_deadline": "Deadline",
                "sla_time_delta_hours": "Hours Remaining / Overdue",
            }),
            use_container_width=True,
            height=280
        )


# =========================================================
# PAGE 4: REGIONAL INSIGHTS
# =========================================================
elif selected_page == "4. Regional Insights":
    render_header(
        "Regional Operational Insights",
        "Comparative benchmark across operating hubs: volume, throughput, resolution velocity, and capacity bottlenecks."
    )

    reg_summary = calculate_regional_summary(df)

    # Summary Dataframe
    st.subheader("Regional Performance Benchmark Table")
    st.dataframe(reg_summary, use_container_width=True)

    st.markdown("---")

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Regional Ticket Volume & Resolution Status")
        reg_status = df.groupby(["region", "status"]).size().reset_index(name="count")
        fig_vol = px.bar(
            reg_status,
            x="region",
            y="count",
            color="status",
            title="Ticket Backlog Distribution by Region",
            template="plotly_dark",
            color_discrete_map={
                "Resolved": "#10b981",
                "In Progress": "#3b82f6",
                "Dispatched": "#f59e0b",
                "Pending Merchant Action": "#a855f7"
            }
        )
        fig_vol.update_layout(xaxis_tickangle=-20, height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_vol, use_container_width=True)

    with col2:
        st.subheader("Average Resolution Time by Region")
        fig_res = px.scatter(
            reg_summary,
            x="Avg Resolution (hrs)",
            y="SLA Compliance (%)",
            size="Total Tickets",
            color="Region",
            text="Region",
            title="Resolution Velocity vs. SLA Compliance (Bubble Size = Ticket Vol)",
            template="plotly_dark",
        )
        fig_res.update_traces(textposition="top center")
        fig_res.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            xaxis=dict(title="Average Resolution Time (Hours)"),
            yaxis=dict(title="SLA Compliance (%)", range=[50, 105]),
        )
        st.plotly_chart(fig_res, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Regional Diagnostic Commentary")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        best_reg = reg_summary.sort_values(by="SLA Compliance (%)", ascending=False).iloc[0]
        st.markdown(f"""
        **Top Performing Region: {best_reg['Region']}**
        - **SLA Compliance:** `{best_reg['SLA Compliance (%)']}%`
        - **Average Resolution Time:** `{best_reg['Avg Resolution (hrs)']} hours`
        - **Total Managed Volume:** `{best_reg['Total Tickets']} tickets`
        - *Driver:* Strong technician route density and rapid closure of peripheral setup requests.
        """)

    with col_d2:
        bottleneck_reg = reg_summary.sort_values(by="SLA Compliance (%)", ascending=True).iloc[0]
        st.markdown(f"""
        **Bottleneck Region: {bottleneck_reg['Region']}**
        - **SLA Compliance:** `{bottleneck_reg['SLA Compliance (%)']}%`
        - **Average Resolution Time:** `{bottleneck_reg['Avg Resolution (hrs)']} hours`
        - **Overdue Backlog:** `{bottleneck_reg['Overdue (Urgent)']} tickets`
        - *Key Action:* Deploy dedicated float technicians to clear terminal hardware swaps.
        """)


# =========================================================
# PAGE 5: METHODOLOGY & SLA SPEC
# =========================================================
elif selected_page == "5. Methodology & SLA Spec":
    render_header(
        "Methodology, SLA Logic & System Specifications",
        "Transparent engineering documentation on synthetic data generation, metric definitions, and operational assumptions."
    )

    st.markdown("""
    ### 1. Project Background & Context
    This dashboard prototype is an **independent concept application** demonstrating modern operational business intelligence for merchant payment terminals (POS). It illustrates how operations leaders can monitor field service efficiency, identify regional technician bottlenecks, and avert customer churn due to terminal downtime.

    > **Disclaimer:** This project is not affiliated with, endorsed by, or representative of any specific digital payments company. All operational metrics, ticket logs, merchant identifiers, and technician names are 100% synthetically generated.

    ---

    ### 2. Synthetic Dataset Generation
    The dataset is generated via `data_generator.py` using controlled random seeds (`seed=42`) ensuring full reproducibility:
    - **Total Sample Size:** 320 distinct service tickets.
    - **Observed Time Window:** 14-day operational rolling window up to reference audit snapshot `2026-10-28 16:00:00`.
    - **Fields Captured:**
      - `ticket_id`: Unique identifier (e.g. `TICK-1001`).
      - `created_at`: Ticket creation timestamp.
      - `region`: Operating hub (`Riyadh Metro`, `Jeddah Coastal`, `Dammam Eastern`, `Makkah Central`, `Medina North`).
      - `issue_type`: Nature of field intervention (`New Terminal Installation`, `Hardware Malfunction`, `Network / Connectivity Offline`, `Software & Firmware Glitch`, `Paper Roll & Peripheral Setup`).
      - `priority`: Incident urgency (`Critical`, `High`, `Medium`, `Low`).
      - `status`: Lifecycle phase (`Resolved`, `In Progress`, `Dispatched`, `Pending Merchant Action`).
      - `assigned_technician`: Field engineer assigned to the ticket.
      - `sla_hours`: Base SLA duration mapped to issue type and priority level.
      - `sla_deadline`: Computed as `created_at + sla_hours`.
      - `resolved_at`: Recorded closure timestamp (or null if currently open).
      - `is_synthetic`: Boolean indicator tagging every record as synthetic.

    ---

    ### 3. Deterministic SLA Risk Rules
    SLA status is assigned deterministically without black-box models:
    | SLA Category | Operational State | Deterministic Rule |
    | :--- | :--- | :--- |
    | **Overdue** | Open / Unresolved | Reference Time > SLA Deadline (`remaining_hours < 0`) |
    | **At Risk** | Open / Unresolved | Reference Time ≤ SLA Deadline AND remaining time ≤ 20% of total SLA duration (`0 <= remaining_hours / sla_hours <= 0.20`) |
    | **Within SLA** | Open or Resolved | (Resolved AND `resolved_at <= sla_deadline`) OR (Open AND `remaining_hours / sla_hours > 0.20`) |
    | **Breached** | Resolved | Resolved AND `resolved_at > sla_deadline` |

    ---

    ### 4. Mathematical Formula for SLA Compliance
    $$\\text{SLA Compliance (\\%)} = \\left( \\frac{\\text{Total Resolved Tickets with } \\text{resolved\\_at} \\le \\text{sla\\_deadline}}{\\text{Total Resolved Tickets}} \\right) \\times 100$$

    - **Denominator:** Strictly resolved tickets. Unresolved tickets are actively monitored in the backlog to prevent artificially inflating or depressing the compliance rate during active work.
    - **Zero-Division Protection:** If no tickets are resolved within a filtered view, compliance safely defaults to 100.0% with zero division errors prevented.

    ---

    ### 5. Architectural Boundaries & Limitations
    - **Local & Offline Execution:** Self-contained application with zero external API dependencies, API keys, or paid services.
    - **No Real-Time Telemetry:** In a production implementation, terminal status would be updated via IoT telemetry feeds and mobile technician app webhooks.
    - **Single Timezone Assumption:** All timestamps are standardized to local operational time (UTC+3 / AST) without cross-border daylight saving shifts.
    """)

    # Interactive sanity check display
    with st.expander("🛠️ Inspect First 10 Raw Synthetic Records"):
        st.dataframe(df.head(10), use_container_width=True)
